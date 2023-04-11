import subprocess
import re
import os
from src.python.util import export_file, execute_cmd


class MaudeComm:
    def __init__(self, direct, maude_path, out_file):
        self.direct = direct
        self.maude_path = maude_path
        self.out_file = out_file

    def comm(self, program, maude_input_file):
        '''Generates a system command to run Maude on the given input file and executes it.'''
        cmd = ['{} {} {}'.format(self.maude_path, program, maude_input_file)]
        return execute_cmd(cmd, self.direct)

    def process_output(self, output):
        '''Parses the output obtained from Maude.'''
        try:
            split = re.search('result (.*?):', output).group(1)
            output = output.split('result {}:'.format(split), 1)[1]
            output = output.split('\nBye.\n', 1)[0]
            output = output.rstrip().lstrip()
            output = output.replace('\n', '').replace('    ', ' ')
            return output
        except Exception:
            return None

    def execute(self, file_name, module, term, clean=False):
        '''
        Generates a Maude command to parse a given term, 
        executes it and returns the parsed result.
        '''
        terms = 'red in {} : {} .'.format(module, term)
        export_file(self.out_file, terms)
        output, error = self.comm(file_name, self.out_file)
        output = self.process_output(output)
        if clean:
            output=remove_unnecessary_parentheses_v12(output)
        if os.path.exists(self.out_file):
            os.remove(self.out_file)

        return output, error


def remove_unnecessary_parentheses(text):
    # Remove the parentheses that appear just before a semicolon
    text = re.sub(r'\s*\)\s*;', ';', text)

    # Remove the parentheses that appear just after a semicolon
    text = re.sub(r';\s*\(', ';', text)

    # Remove parentheses if there is only whitespace between them
    text = re.sub(r'\(\s*\)', '', text)

    # Remove any remaining leading or trailing whitespace
    text = text.strip()

    return text


def remove_unnecessary_parentheses_v2(text):
    count = 0
    result = []

    for char in text:
        if char == '(':
            count += 1
        elif char == ')':
            count -= 1
        elif count == 0:
            result.append(char)

    return ''.join(result).strip()


def remove_unnecessary_parentheses_v3(text):
    stack = []
    result = []
    skip = False

    for char in text:
        if skip:
            skip = False
            continue

        if char == '(':
            if not stack or stack[-1] != ';':
                result.append(char)
            stack.append(char)
        elif char == ')':
            stack.pop()
            if not stack or stack[-1] != ';':
                result.append(char)
        elif char == ';':
            stack.append(char)
            result.append(char)
            skip = True
        else:
            result.append(char)

    return ''.join(result).strip()


def remove_unnecessary_parentheses_v4(text):
    count = 0
    result = []

    for char in text:
        if char == '(':
            if count > 0:
                count += 1
            else:
                count += 1
                result.append(char)
        elif char == ')':
            if count > 1:
                count -= 1
            else:
                count -= 1
                result.append(char)
        elif char == ';':
            if count > 0:
                count -= 1
            result.append(char)
        else:
            result.append(char)

    return ''.join(result).strip()


def remove_unnecessary_parentheses_v5(text):
    stack = []
    result = []

    for char in text:
        if char == '(':
            stack.append(char)
        elif char == ')':
            if stack and stack[-1] == '(':
                stack.pop()
            else:
                result.append(char)
        else:
            result.append(char)

    return ''.join(result).strip()


def remove_unnecessary_parentheses_v6(text):
    result = []
    paren_stack = []

    for idx, char in enumerate(text):
        if char == '(':
            if idx + 1 < len(text) and text[idx + 1] == '\n':
                continue
            paren_stack.append(char)
            result.append(char)
        elif char == ')':
            if paren_stack:
                paren_stack.pop()
                result.append(char)
        else:
            result.append(char)

    return ''.join(result).strip()


def remove_unnecessary_parentheses_v9(text):
    result = []
    text_lines = text.split('\n')
    close_parentheses = 0

    for line in reversed(text_lines):
        line = line.strip()
        if line.endswith(')') and close_parentheses > 0:
            close_parentheses -= 1
        elif line.endswith(';'):
            if close_parentheses > 0:
                close_parentheses -= 1
                result.append(')')
            result.append(line)
        else:
            result.append(line)
            if line.endswith('('):
                close_parentheses += 1

    return '\n'.join(reversed(result)).strip()


def remove_unnecessary_parentheses_v11(text):
    result = []
    close_parentheses_to_remove = 0

    for i in reversed(range(len(text))):
        char = text[i]

        if char == ')':
            if close_parentheses_to_remove > 0:
                close_parentheses_to_remove -= 1
            else:
                result.append(char)
        elif char == '(':
            if i < len(text) - 1 and text[i + 1] == ')':
                close_parentheses_to_remove += 1
            else:
                result.append(char)
        else:
            result.append(char)

    return ''.join(reversed(result)).strip()


def remove_unnecessary_parentheses_v12(text):
    result = []
    num_consecutive_closing = 0
    open_parentheses_to_remove = 0

    for char in reversed(text):
        if char == ')':
            num_consecutive_closing += 1
        else:
            break


    for char in reversed(text[:-num_consecutive_closing]):
        if char == ')':
            break
        elif char == "(":
            num_consecutive_closing = num_consecutive_closing -1
            break
    currently_inside_count = 0

    if num_consecutive_closing == 0:
        return text
    for char in reversed(text[:-num_consecutive_closing]):
        if not num_consecutive_closing:
            result.append(char)
            continue
        if char == '(':
            if currently_inside_count and num_consecutive_closing:
                result.append(char)
                currently_inside_count -= 1
            else:
                num_consecutive_closing -= 1
        elif char == ')':
            currently_inside_count += 1
            result.append(char)
        else:
            result.append(char)

    return ''.join(result)[::-1]
