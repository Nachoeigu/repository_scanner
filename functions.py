import logging


# Define a custom log formatter that includes only the message
class MessageOnlyFormatter(logging.Formatter):
    def format(self, record):
        return record.getMessage()

# Configure the logging module with the custom formatter
logging.basicConfig(
    level=logging.INFO,  # Set the desired logging level
    format='%(message)s',  # Use the custom formatter to show only the message
    handlers=[
        logging.FileHandler('input_for_chatgpt.txt', mode = 'w'),  # Specify the log file name
        logging.StreamHandler()  # Add a stream handler to print log messages to the console
    ]
)

class PrompterEngineer:

    def __init__(self, character_limits_per_message=25000):
        self.CHARACTER_LIMIT_IN_CHATGPT = character_limits_per_message

    def generate_main_context(self, context_msg):
        self.context = context_msg
    
    def etl_entire_text(self, message):
        """
        This function receives an entire message with the details of the repository.
        It outputs the message with a split based on characters about limit in chatgpt
        """
        messages = message.split('---SPLIT_LINE_THAT_WE_USE_LETTER_FOR_ETL_PROCCESS----')

        repository_structure = messages[0]
        files_content = messages[1]
        logging.info(repository_structure)

        if len(files_content) > self.CHARACTER_LIMIT_IN_CHATGPT:
            output = []
            n_iteration = len([_ for _ in range(0, len(files_content), self.CHARACTER_LIMIT_IN_CHATGPT)]) - 1
            for idx, step in enumerate(range(0, len(files_content), self.CHARACTER_LIMIT_IN_CHATGPT)):
                if idx == n_iteration:
                    #last message
                    output.append(f'Continuation of the last message: ' + file_content[step : step + self.CHARACTER_LIMIT_IN_CHATGPT])
                elif idx == 0:
                    output.append(file_content[step : step + self.CHARACTER_LIMIT_IN_CHATGPT] + '  ... (this continues in the next message)')
                else:
                    output.append(f'Continuation of the last message: ' + file_content[step : step + self.CHARACTER_LIMIT_IN_CHATGPT] + '  ... (this continues in the next message)')

        else:
            output.append(files_content)

        for msg in output:
            logging.info(msg)
        print('--')


if __name__ == '__main__':
    with open('logfile.txt','r') as file:
        file_content = file.read()

    PrompterEngineer().etl_entire_text(file_content)

 
