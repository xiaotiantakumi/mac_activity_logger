import subprocess
import time
import os

def run_applescript(script):
    process = subprocess.Popen(['osascript', '-e', script], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return out.decode('utf-8'), err.decode('utf-8')

def test_gui_launch():
    print("Testing GUI launch...")
    
    # Start the GUI in background
    # Note: We use 'python' or 'uv run'
    gui_process = subprocess.Popen(['uv', 'run', 'src/logger/presentation/gui.py'])
    
    time.sleep(5) # Wait for launch
    
    try:
        # Check if window exists via AppleScript
        check_script = """
        tell application "System Events"
            tell process "Python"
                set winNames to name of every window
                return winNames
            end tell
        end tell
        """
        out, err = run_applescript(check_script)
        print(f"Windows found: {out}")
        
        if "macOS Activity Logger" in out:
            print("✅ GUI Window detected!")
        else:
            print("❌ GUI Window NOT detected.")
            # Flutter apps might name the process differently or window title might be different in System Events
            
        # Try to click Start Monitoring (This is highly dependent on Accessibility labels)
        click_script = """
        tell application "System Events"
            tell process "Python"
                click button "Start Monitoring" of window 1
            end tell
        end tell
        """
        # out, err = run_applescript(click_script)
        # print(f"Click attempt output: {out} {err}")

    finally:
        gui_process.terminate()
        print("GUI process terminated.")

if __name__ == "__main__":
    test_gui_launch()
