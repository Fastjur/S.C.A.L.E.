from random_file_creator import RandomFileCreator

PRE_CREATED_RANDOM_FILES_DIR = "pre-created-random-files"

num_files = input("Enter number of files to create: ")
num_files = int(num_files)

random_file_creator = RandomFileCreator(save_dir=PRE_CREATED_RANDOM_FILES_DIR)
for i in range(num_files):
    print(f"Creating random file {i + 1:d}/{num_files:d}")
    random_file_creator.create_random_file(1, 3)
