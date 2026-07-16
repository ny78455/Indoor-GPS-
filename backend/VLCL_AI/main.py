import sys
import os

# Add root folder to paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from examples.demo_environment import run_demo

if __name__ == "__main__":
    run_demo()
