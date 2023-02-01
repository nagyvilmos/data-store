from ._test import test, assert_all, assert_pass, assert_equal
from data_access_layer import DataAccessLayer#, pretty_print_bytes
import os
        
def create_dal():
    return DataAccessLayer("test.db")

def close_dal(dal:DataAccessLayer):
    dal.close()
    return (True,None)

def destroy_dal(dal:DataAccessLayer):
    dal.close()
    if os.path.isfile(dal.file_name):
        os.remove(dal.file_name)
    return (True,None)

@test("create dal", create_dal, destroy_dal)
def test_create_dal(dal:DataAccessLayer):
    return assert_pass(dal is not None and os.path.isfile(dal.file_name),"Failed to create dal")

@test("create page", create_dal, close_dal)
def test_create_page(dal:DataAccessLayer):
    page=dal.new_page()
    page.data[555]=99
    dal.write_page(page)
    return assert_equal(dal.page_count(),1, "Content was not created")

def lots_of_numbers():
    return range(0,200)
@test("Update the page", create_dal, close_dal, lots_of_numbers)
def test_add_number(dal:DataAccessLayer, step:int):
    page=dal.read_page(1)
    page.data[step]=255-step
    dal.write_page(page)
    return assert_equal(page.data[step],255-step, "Item was not added")

@test("Update lots on the page", create_dal, close_dal)
def test_lots(dal:DataAccessLayer):
    page=dal.read_page(1)
    tests=[]
    for step in lots_of_numbers():
        page.data[step]=(step+128)%256
        tests.append(assert_equal(page.data[step],(step+128)%256, f"{step} was not added"))
    dal.write_page(page)
    return assert_all(tests)

@test("read page", create_dal, destroy_dal)
def test_has_content(dal:DataAccessLayer):
    page=dal.read_page(1)
    return assert_all([
        assert_equal(
            page.page_number , 1,
            "Returned page has wrong index"),
        assert_equal(
            page.data[555] , 99,
            "Returned page has incorrect content")])

@test("access deleted stack", create_dal, destroy_dal)
def test_has_content(dal:DataAccessLayer):
    first=dal.new_page()
    dal.write_page(first)
    results=[assert_equal(
            first.page_number, 1,
            "First page saved")]
    second=dal.new_page()
    dal.write_page(second)    
    results.append(assert_equal(
            second.page_number, 2,
            "Second page saved"))
    dal.delete_page(first)
    results.append(assert_equal(
            first.page_number, -1,
            "First page deleted"))
    third=dal.new_page()
    dal.write_page(third)
    results.append(assert_equal(
            third.page_number, 1,
            "Third page saved"))
    dal.delete_page(second)
    results.append(assert_equal(
            second.page_number, -1,
            "Second page deleted"))
    return assert_all(results +[
        assert_equal(
            dal.page_count(), 2,
            "Page count == 2"),
        assert_equal(
            dal.free_pages(), 1,
            "Free pages == 1"),
        assert_equal(
            dal.free_list.percent_free(), 50,
            "Percent free == 50")])