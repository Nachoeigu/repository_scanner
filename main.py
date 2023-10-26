import os
from config import *
import logging

logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO (or your desired level)
    handlers=[
        logging.FileHandler('logfile.txt'),  # Specify the log file name
        logging.StreamHandler()  # Add a stream handler to print log messages to the console
    ]
)



def printing_files(root, files, ignore_files):
    for file in files:

        if file.lower() in [item.lower() for item in ignore_files]:
            continue
        file_path = os.path.join(root, file)
        logging.info(f" THE FILE NAMED '{file}' CONTAINS THE FOLLOWING INFORMATION (IT IS BELOW) ")
        # Print the content of each file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            logging.info('```')
            logging.info(content)
            logging.info('```')

def print_directory_structure_and_file_contents(directory, ignore_files=[], ignore_directories=[]):
    for root, dirs, files in os.walk(directory):
        if any(word in root for word in ignore_directories):
            continue
        # Print the files in the current directory
        printing_files(root, files, ignore_files)

def print_directory_structure(directory, indent="", printed_dirs = set(), first_approach = False):
    for root, dirs, files in os.walk(directory):
        current_dir = os.path.basename(root)
        if current_dir not in printed_dirs:
            if first_approach:
                logging.info(f"{indent}{current_dir} (DIRECTORY)")
            else:
                logging.info(f"{indent}|__ {current_dir} (DIRECTORY)")
            printed_dirs.add(current_dir)
            for file in files:
                logging.info(f"{indent}   |__ {file} (FILE)")
            for d in dirs:
                new_indent = indent + "   "
                print_directory_structure(os.path.join(root, d), new_indent, printed_dirs, first_approach=False)

if __name__ == "__main__":
    target_directory = input('Put your entire path:')
    logging.info("THIS IS THE STRUCTURE OF THE ENTIRE PROJECT:")    
    print_directory_structure(target_directory, first_approach=True)
    logging.info("Did you understand perfectly the structure of the project I provided to you above?")    
    
    logging.info('-----------------------------------------------------------------------------')

    logging.info("IN THE FOLLOWING MESSAGES, I WILL SHARE WITH YOU THE CONTENT OF EACH FILE:")
    print_directory_structure_and_file_contents(target_directory, 
                                                ignore_files = FILES_TO_IGNORE,
                                                ignore_directories= DIRECTORIES_TO_IGNORE)