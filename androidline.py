import os
import subprocess
import sys
import shutil
from tqdm import tqdm

# Helper function to print colored messages
def print_colored(message, color):
    colors = {
        'green': '\033[32m',
        'yellow': '\033[33m',
        'red': '\033[31m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['reset'])}{message}{colors['reset']}")

# Function to clone the template repository and set up the project
def clone_template(template_repo, project_name):
    print_colored(f"Cloning template repository: {template_repo}", 'yellow')
    result = subprocess.run(['git', 'clone', template_repo, project_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        print_colored(f"Error: Failed to clone the repository.", 'red')
        sys.exit(1)

# Function to customize the project with user input
def customize_project(project_name, package_name, min_sdk, target_sdk):
    project_path = os.path.join(os.getcwd(), project_name)
    build_gradle = os.path.join(project_path, 'app', 'build.gradle')

    # Check if build.gradle exists, if not create it
    if not os.path.exists(build_gradle):
        print_colored("Error: build.gradle is missing. Creating default build.gradle.", 'yellow')
        create_default_build_gradle(project_path, package_name, min_sdk, target_sdk)

    # Modify build.gradle to use the provided package_name, minSdk, and targetSdk
    with open(build_gradle, 'r') as f:
        build_content = f.read()

    build_content = build_content.replace("com.example.app", package_name)
    build_content = build_content.replace("minSdkVersion 21", f"minSdkVersion {min_sdk}")
    build_content = build_content.replace("targetSdkVersion 30", f"targetSdkVersion {target_sdk}")

    with open(build_gradle, 'w') as f:
        f.write(build_content)

    print_colored(f"Project {project_name} customized with package name {package_name}, minSdk {min_sdk}, targetSdk {target_sdk}.", 'green')

# Function to create a default build.gradle if missing
def create_default_build_gradle(project_path, package_name, min_sdk, target_sdk):
    build_gradle_content = f"""
apply plugin: 'com.android.application'

android {{
    compileSdkVersion 30
    defaultConfig {{
        applicationId "{package_name}"
        minSdkVersion {min_sdk}
        targetSdkVersion {target_sdk}
        versionCode 1
        versionName "1.0"
    }}
    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }}
        debug {{
            debuggable true
        }}
    }}
}}

dependencies {{
    implementation 'com.android.support:appcompat-v7:28.0.0'
}}
"""
    app_path = os.path.join(project_path, 'app')
    if not os.path.exists(app_path):
        os.makedirs(app_path)

    with open(os.path.join(app_path, 'build.gradle'), 'w') as f:
        f.write(build_gradle_content)

# Function to ensure gradlew is available and set permissions
def ensure_gradlew(project_name):
    gradlew_path = os.path.join(project_name, 'gradlew')

    # If gradlew doesn't exist, try to generate it using gradle wrapper
    if not os.path.exists(gradlew_path):
        print_colored("gradlew not found. Running 'gradle wrapper' to generate it...", 'yellow')
        result = subprocess.run(['gradle', 'wrapper'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project_name)
        if result.returncode != 0:
            print_colored("Error: Failed to generate gradle wrapper. Make sure Gradle is installed.", 'red')
            sys.exit(1)
    
    # Check if gradlew exists and try to set executable permissions
    if os.path.exists(gradlew_path):
        print_colored("Checking permissions for gradlew...", 'yellow')
        result = subprocess.run(['ls', '-l', gradlew_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            print_colored("Error: Failed to check gradlew permissions.", 'red')
            sys.exit(1)

        permissions = result.stdout.decode().strip()
        if 'x' not in permissions:
            print_colored("gradlew does not have execute permissions. Attempting to set them...", 'yellow')
            result = subprocess.run(['chmod', '+x', gradlew_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project_name)
            if result.returncode != 0:
                print_colored("Error: Failed to set executable permissions for gradlew. Please try setting permissions manually.", 'red')
                sys.exit(1)
        else:
            print_colored("gradlew already has executable permissions.", 'green')
    else:
        print_colored("gradlew not found even after running gradle wrapper. Please check the project directory.", 'red')
        sys.exit(1)

# Function to compile the project using gradlew
def compile_project(project_name):
    project_path = os.path.join(os.getcwd(), project_name)
    gradlew_path = os.path.join(project_path, 'gradlew')

    # Ensure gradlew is available and has execute permissions
    ensure_gradlew(project_name)

    print_colored(f"Compiling project {project_name} using gradlew...", 'yellow')
    with tqdm(total=100, desc="Building Project", ncols=100, bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [elapsed: {elapsed}]") as pbar:
        result = subprocess.run(['sh', gradlew_path, 'assembleDebug'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project_path)

        if result.returncode != 0:
            print_colored("Error: Gradle build failed.", 'red')
            print_colored(f"Gradle error output: {result.stderr.decode()}", 'red')  # Show the error message
            sys.exit(1)

        pbar.update(100)
        print_colored("Build successful!", 'green')

        # Check if APK is generated
        apk_path = os.path.join(project_path, 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
        if os.path.exists(apk_path):
            print_colored(f"APK successfully built: {apk_path}", 'green')
        else:
            print_colored("Error: APK not found. Build might have failed.", 'red')

# Main function to handle user input and call necessary functions
def main():
    if len(sys.argv) != 5:
        print_colored("Usage: python androidline.py <project_name> <package_name> <min_sdk> <target_sdk>", 'red')
        sys.exit(1)

    project_name = sys.argv[1]
    package_name = sys.argv[2]
    min_sdk = sys.argv[3]
    target_sdk = sys.argv[4]

    template_repo = "https://github.com/H4-Corp/android-template-for-al.git"

    print_colored(f"Arguments received: {sys.argv}", 'yellow')

    # Step 1: Create project directory and clone template
    print_colored(f"Creating project directory: {project_name}", 'yellow')
    os.makedirs(project_name, exist_ok=True)

    # Clone template repository
    clone_template(template_repo, project_name)

    # Step 2: Customize the project
    customize_project(project_name, package_name, min_sdk, target_sdk)

    # Step 3: Compile the project
    compile_project(project_name)

if __name__ == "__main__":
    main()
