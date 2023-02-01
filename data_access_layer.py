# Source for the idea: https://betterprogramming.pub/build-a-nosql-database-from-the-scratch-in-1000-lines-of-code-8ed1c15ed924
INT_SIZE = 4 # this is 2**31-1 or 2147483647
NEW_PAGE = -1

def f_hex(num, size):
    return ('00000000' + hex(num)[2:].upper())[-size:]

def pretty_print_bytes (data, title=None):
    size=len(data)
    last=bytearray(0)
    repeat=True
    if title is not None:
        print("="*78)
        print(title)
    print("-"*78)    
    for offset in range(0,size,16):
        sub_set=data[offset:offset+16]
        if sub_set == last:
            if not repeat:
                print(" *")
                repeat=True
            continue
        last=sub_set
        repeat=False
        print(f_hex(offset,8), end='  ')
        for x in range(16):
            print(f_hex(sub_set[x],2) if x < len(sub_set) else '  ', end=' ' if x%8 != 7 else '  ')
        print('|',end='')
        text = sub_set.decode('utf-8')
        for x in range(16):
            if x < len(text):
                c= text[x]
                print(c if c.isprintable() else '.', end='')
            else:
                print(' ',end='')
        print('|')
    print("-"*78)    

def int_to_bytes(number:int, size=INT_SIZE, signed=True) -> bytes: 
    return number.to_bytes(size, "big", signed=signed)

def bytes_to_int(number:bytes,signed=True) -> int: 
    return int.from_bytes(number,"big", signed=signed)

class Page:
    def __init__(self, data:bytearray, page_number:int=NEW_PAGE) -> None:
        self.data=data
        self.page_number=page_number

    def dump(self, title=None):
        pretty_print_bytes(self.data, title if title is not None else f'Page #{self.page_number}')
    def read(self, pos:int, size:int) -> bytes:
        return self.data[pos:pos+size]

    def read_int(self, pos:int, size=INT_SIZE, signed=True) -> int:
        return bytes_to_int(self.read(pos,size),signed)    

    def write(self, pos:int, value:bytes) -> None:
        self.data[pos:pos+len(value)]=value

    def write_int(self, pos:int, value:int, size=INT_SIZE, signed=True) -> None:
        self.write(pos,int_to_bytes(value,size,signed))    
#Page

class FreeList:
    def __init__(self, dal:'DataAccessLayer', page:Page) -> None:
        self.dal=dal
        self.page=page
        self.max_page=page.read_int(0,signed=False) if page.page_number==0 else 0
        self.free_pages=page.read_int(4,signed=False) if page.page_number==0 else 0
        self.first_free=page.read_int(8,signed=False) if page.page_number==0 and self.free_pages>0 else 0
        page.page_number=0

    def _write_update(self,page:Page=None):
        self.page.write_int(0,self.max_page,signed=False)
        self.page.write_int(4,self.free_pages,signed=False)
        self.page.write_int(8,self.first_free,signed=False)
        self.dal.write_page(self.page)
        if page is not None:
            self.dal.write_page(page)

    def delete_page(self,page:Page)-> None:
        if page.page_number==NEW_PAGE:
            return
        # add the page to the stack//
        page.data=bytearray(len(page.data))
        page.write_int(0,self.first_free,signed=False)
        self.first_free=page.page_number
        self.free_pages=self.free_pages+1
        self._write_update(page)
        page.write_int(0,0,signed=False)
        page.page_number=NEW_PAGE # is now a new page

    def get_next_free(self):
        if self.first_free != 0:
            next_page = self.first_free
            page=self.dal.read_page(next_page)
            self.first_free=page.read_int(0,signed=False)
            self.free_pages=self.free_pages-1
            self._write_update(page)
            return next_page
        self.max_page=self.max_page+1
        self._write_update()
        return self.max_page

    def page_count(self):
        return self.max_page

    def percent_free(self):
        return 100*self.free_pages/self.max_page if self.max_page > 0 else 0
#FreeList

class DataAccessLayer:
    def __init__(self, file_name:str, page_size:int = 4096) -> None:
        self.file_name=file_name
        self.page_size=page_size
        self.handle=open(self.file_name,'a+b',buffering=self.page_size*4)
        self.handle.seek(0,2)
        size=self.handle.tell()
        page:Page=None
        if size > 0:
            page=self.read_page(0)
        else:
            page=self.new_page()
        self.free_list = FreeList(self, page)

    def close(self) -> None:
        if self.handle is None:
            return
        self.handle.close()
        self.handle=None

    def delete_page(self,page:Page)-> None:
        self.free_list.delete_page(page)

    def free_pages(self):
        return self.free_list.free_pages

    def new_page(self) -> Page:
        return Page( bytearray(self.page_size))

    def page_count(self):
        return self.free_list.page_count()

    def read_page(self, page_number:int) -> Page:
        self.handle.seek(self.page_size*page_number)
        data = bytearray(self.handle.read(self.page_size))
        return Page(data, page_number)

    def write_page(self,page:Page)-> None:
        #pretty_print_bytes(page.data, f'Page {page.page_number}')
        if page.page_number == NEW_PAGE:
            page.page_number=self.free_list.get_next_free()
        self.handle.seek(self.page_size*page.page_number)
        self.handle.write(bytes(page.data))
        self.handle.flush()
#DataAccessLayer
