# log_viewer.py
"""
Simple log viewer for COE API logs
Provides real-time log monitoring and filtering
"""

import os
import time
import sys
from datetime import datetime

def print_colored(text, color_code):
    """Print colored text"""
    print(f"\033[{color_code}m{text}\033[0m")

def get_log_color(line):
    """Determine color based on log level and content"""
    if "ERROR" in line or "❌" in line:
        return "91"  # Red
    elif "WARNING" in line or "⚠️" in line:
        return "93"  # Yellow
    elif "INFO" in line and any(emoji in line for emoji in ["✅", "🚀", "📊"]):
        return "92"  # Green
    elif "📥" in line or "📤" in line:
        return "94"  # Blue
    else:
        return "0"   # Default

def tail_file(filename, lines=10):
    """Tail a file similar to Unix tail command"""
    if not os.path.exists(filename):
        print(f"Log file '{filename}' not found!")
        return
    
    with open(filename, 'r', encoding='utf-8') as f:
        # Go to end of file
        f.seek(0, 2)
        file_size = f.tell()
        
        # Find the last n lines
        lines_found = 0
        buffer = ""
        
        for i in range(file_size):
            f.seek(file_size - i - 1)
            char = f.read(1)
            buffer = char + buffer
            
            if char == '\n':
                lines_found += 1
                if lines_found >= lines:
                    break
        
        # Print the lines
        for line in buffer.strip().split('\n'):
            if line.strip():
                color = get_log_color(line)
                print_colored(line, color)

def watch_logs(filename, follow=True):
    """Watch log file for new entries"""
    if not os.path.exists(filename):
        print(f"Log file '{filename}' not found!")
        return
    
    print(f"Watching {filename} (Press Ctrl+C to stop)")
    print("-" * 80)
    
    # Show last 20 lines first
    tail_file(filename, 20)
    print("-" * 80)
    
    if not follow:
        return
    
    # Follow new lines
    with open(filename, 'r', encoding='utf-8') as f:
        # Go to end of file
        f.seek(0, 2)
        
        try:
            while True:
                line = f.readline()
                if line:
                    color = get_log_color(line)
                    print_colored(line.rstrip(), color)
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nLog watching stopped.")

def filter_logs(filename, filter_term, case_sensitive=False):
    """Filter logs by search term"""
    if not os.path.exists(filename):
        print(f"Log file '{filename}' not found!")
        return
    
    print(f"Filtering '{filename}' for: '{filter_term}'")
    print("-" * 80)
    
    count = 0
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            search_line = line if case_sensitive else line.lower()
            search_term = filter_term if case_sensitive else filter_term.lower()
            
            if search_term in search_line:
                count += 1
                color = get_log_color(line)
                print_colored(f"[{line_num:4d}] {line.rstrip()}", color)
    
    print("-" * 80)
    print(f"Found {count} matching lines")

def show_log_stats(filename):
    """Show log file statistics"""
    if not os.path.exists(filename):
        print(f"Log file '{filename}' not found!")
        return
    
    stats = {
        'total_lines': 0,
        'info_lines': 0,
        'warning_lines': 0,
        'error_lines': 0,
        'request_lines': 0,
        'response_lines': 0,
        'file_size': os.path.getsize(filename)
    }
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            stats['total_lines'] += 1
            
            if 'INFO' in line:
                stats['info_lines'] += 1
            elif 'WARNING' in line:
                stats['warning_lines'] += 1
            elif 'ERROR' in line:
                stats['error_lines'] += 1
            
            if '📥' in line:
                stats['request_lines'] += 1
            elif '📤' in line:
                stats['response_lines'] += 1
    
    print(f"Log Statistics for: {filename}")
    print("=" * 50)
    print(f"File Size:     {stats['file_size']:,} bytes")
    print(f"Total Lines:   {stats['total_lines']:,}")
    print(f"INFO:          {stats['info_lines']:,}")
    print(f"WARNING:       {stats['warning_lines']:,}")
    print(f"ERROR:         {stats['error_lines']:,}")
    print(f"Requests:      {stats['request_lines']:,}")
    print(f"Responses:     {stats['response_lines']:,}")
    
    if stats['total_lines'] > 0:
        error_rate = (stats['error_lines'] / stats['total_lines']) * 100
        print(f"Error Rate:    {error_rate:.2f}%")

def main():
    """Main function with menu"""
    print("=" * 60)
    print("🔍 COE API Log Viewer")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "watch":
            log_file = sys.argv[2] if len(sys.argv) > 2 else "logs/app.log"
            watch_logs(log_file)
        elif command == "tail":
            log_file = sys.argv[2] if len(sys.argv) > 2 else "logs/app.log"
            lines = int(sys.argv[3]) if len(sys.argv) > 3 else 20
            tail_file(log_file, lines)
        elif command == "filter":
            if len(sys.argv) < 3:
                print("Usage: python log_viewer.py filter <search_term> [log_file]")
                return
            search_term = sys.argv[2]
            log_file = sys.argv[3] if len(sys.argv) > 3 else "logs/app.log"
            filter_logs(log_file, search_term)
        elif command == "stats":
            log_file = sys.argv[2] if len(sys.argv) > 2 else "logs/app.log"
            show_log_stats(log_file)
        else:
            print(f"Unknown command: {command}")
    else:
        # Interactive mode
        while True:
            print("\nChoose an option:")
            print("1. Watch logs (real-time)")
            print("2. Show last 20 lines")
            print("3. Filter logs")
            print("4. Show statistics")
            print("5. Exit")
            
            choice = input("\nEnter choice (1-5): ").strip()
            
            if choice == "1":
                log_file = input("Log file (default: logs/app.log): ").strip()
                if not log_file:
                    log_file = "logs/app.log"
                watch_logs(log_file)
            
            elif choice == "2":
                log_file = input("Log file (default: logs/app.log): ").strip()
                if not log_file:
                    log_file = "logs/app.log"
                lines = input("Number of lines (default: 20): ").strip()
                lines = int(lines) if lines.isdigit() else 20
                tail_file(log_file, lines)
            
            elif choice == "3":
                log_file = input("Log file (default: logs/app.log): ").strip()
                if not log_file:
                    log_file = "logs/app.log"
                search_term = input("Search term: ").strip()
                if search_term:
                    filter_logs(log_file, search_term)
            
            elif choice == "4":
                log_file = input("Log file (default: logs/app.log): ").strip()
                if not log_file:
                    log_file = "logs/app.log"
                show_log_stats(log_file)
            
            elif choice == "5":
                print("Goodbye!")
                break
            
            else:
                print("Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")

# Usage examples:
# python log_viewer.py                          # Interactive mode
# python log_viewer.py watch                    # Watch app.log
# python log_viewer.py watch logs/error.log     # Watch error.log
# python log_viewer.py tail logs/app.log 50     # Show last 50 lines
# python log_viewer.py filter "ERROR"           # Filter for errors
# python log_viewer.py stats                    # Show statistics
