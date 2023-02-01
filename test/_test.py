from datetime import datetime
#import logging
import traceback
import os
#log = logging.getLogger('test')
#log.setLevel(logging.DEBUG)

test_funcs = []

def trace_to_json(trace):
    stack = []
    for frame_summary, line_no in traceback.walk_tb(trace):
        filename = frame_summary.f_code.co_filename
        if filename and not filename.startswith("<"):
            filename = os.path.abspath(filename)
        stack.append({
            "filename": filename or "?",
            "lineno":line_no,
            "name": frame_summary.f_code.co_name
        })
    return stack

def assert_all(assertions):
    messages=[]
    for assertion in assertions:
        if not assertion[0]:
            messages.append(assertion[1])
    return (False,"; ".join(messages)) if len(messages) > 0 else (True,None)

def assert_any(assertions):
    for assertion in assertions:
        if not assertion[0]:
            return assertion
    return (True,None)

def assert_equal(result, expected, message: str):
    return assert_pass(result == expected, f'{message};result={result},  expected={expected}')

def assert_pass(passed: bool, message: str):
    return (passed,message if not passed else None)

def test(description, scafold=None, cleanup=None, itteration=None):
    #log.debug(f"wrap {description}")
    def test_decorator(test):
        def wrapper(test_name):
            if test_name is not None and test_name != description:
                return None
                
            #log.info('=====Test: ' + description)
            def run_test(step):
                doc = {
                    'test':description if step == None else f'{description} - {step}',
                    'passed':False,
                    'finished':False,
                    'started':datetime.now()}
                try:
                    context=scafold() if scafold is not None else None
                    try:
                        if (step is None):
                            result = test(context) if context is not None else test()
                        else:
                            result = test(context,step) if context is not None else test(step)
                        doc['passed']=result[0]
                        if not result[0]:
                            doc['message']=result[1]
                        doc['finished']=True
                    except Exception as ex:
                        print(str(ex))
                        doc['test_exception'] = str(ex)
                        doc['test_traceback'] = trace_to_json(ex.__traceback__)
                        doc['passed']=False
                        doc['finished']=False
                    clean=cleanup(context) if cleanup else (True,None)
                    doc['clean']=clean[0]
                    if not clean[0]:
                        doc['clean_message']=clean[1]
                except Exception as ex:
                    print(str(ex))
                    doc['scafold_exception'] = str(ex)
                    doc['scafold_traceback'] = trace_to_json(ex.__traceback__)
                    doc['clean']=False
                doc['completed'] = datetime.now()
                doc['elapsed'] = (doc['completed'] - doc['started']).total_seconds()
                doc['completed']=doc['completed'].isoformat()
                doc['started']=doc['started'].isoformat()
                return doc
            if itteration == None:
                return [run_test(None)]
            return [run_test(step) for step in itteration()]
        # add the wrapper to the list of migrations
        # if it hasn't already been called, then it will
        # be called once and recorded in the database
        test_funcs.append(wrapper)
        return test
    return test_decorator
