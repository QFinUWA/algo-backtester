

class File:

    def __init__(self, name, size):
        self.name = name
        self.size = size


class Group:

    def __init__(self):
        self.files = []
        self.size = 0
    
        
    def add_file(self, file: File):
        self.files.append(file.name)
        self.size += file.size

database = {
    'group1': Group(),
    'group2': Group(),
    'group3': Group()
}

total_size = 0

def add_file_to_group(file: File, group: str):
    global total_size
    total_size += file.size
    database[group].add_file(file)

def get_group_size(group: str):
    return database[group].size
    

def top_n(n):
    return sorted((g for g in database), key=lambda x: database[x].size, reverse=True)[:n]


# test
file1 = File('file1', 100)
file2 = File('file2', 200)
file3 = File('file3', 300)
file4 = File('file4', 400)

add_file_to_group(file1, 'group1')
add_file_to_group(file2, 'group1')
add_file_to_group(file3, 'group2')
add_file_to_group(file4, 'group3')

print(get_group_size('group1'))
print(get_group_size('group2'))
print(get_group_size('group3'))

print(top_n(2))