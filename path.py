#!/usr/bin/python3.7

import os

currentDir = os.path.dirname(__file__)

def to(relativePath):
    return os.path.join(currentDir, relativePath)
