#!/usr/bin/env python3
import sys
import os
import argparse

def generate_file(size_in_mb, file_name):
  mega_byte = 1_000_000
  with open(file_name, 'wb') as file:
    file.write(os.urandom(size_in_mb*mega_byte))


def main():
  parser = argparse.ArgumentParser(description='Generate file with a given name and size (in megabytes)')
  parser.add_argument('-s', type=int, required=True, dest='size', help='Size of the file (in megabytes)')
  parser.add_argument('-n', type=str, required=True, dest='name', help='Name of the file')

  arguments = parser.parse_args()
  generate_file(arguments.size, arguments.name)


if __name__ == '__main__':
  main()