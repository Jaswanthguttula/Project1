"""
Installation and Setup Script
"""

import os
import sys
import subprocess


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'=' * 60}")
    print(f"{description}")
    print(f"{'=' * 60}")

    try:
        result = subprocess.run(
            command, shell=True, check=True, capture_output=True, text=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(e.stderr)
        return False


def main():
    """Main setup function"""
    print("Contract Clause Detection System - Setup")
    print("=" * 60)

    # Step 1: Check Python version
    print(f"\nPython version: {sys.version}")
    if sys.version_info < (3, 8):
        print("ERROR: Python 3.8 or higher is required")
        return

    # Step 2: Create virtual environment
    if not os.path.exists("venv"):
        print("\nCreating virtual environment...")
        if not run_command("python -m venv venv", "Creating virtual environment"):
            return
    else:
        print("\nVirtual environment already exists")

    # Step 3: Determine activation command based on OS
    if os.name == "nt":  # Windows
        activate_cmd = r"venv\Scripts\activate"
        pip_cmd = r"venv\Scripts\pip"
        python_cmd = r"venv\Scripts\python"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"

    print(f"\nTo activate the virtual environment, run:")
    print(f"  {activate_cmd}")

    # Step 4: Upgrade pip
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")

    # Step 5: Install dependencies
    if not run_command(
        f"{pip_cmd} install -r requirements.txt", "Installing dependencies"
    ):
        print("\nWARNING: Some dependencies failed to install")
        print("You may need to install them manually")

    # Step 6: Download spaCy model
    print("\nDownloading spaCy language model...")
    run_command(
        f"{python_cmd} -m spacy download en_core_web_lg", "Downloading spaCy model"
    )

    # Step 7: Create necessary directories
    print("\nCreating directories...")
    directories = ["uploads", "generated_reports", "temp_files", "tests"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"  Created: {directory}")

    # Step 8: Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("\nCreating .env file from template...")
        if os.path.exists(".env.example"):
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("  .env file created")
        else:
            print("  WARNING: .env.example not found")

    # Step 9: Initialize database
    print("\nInitializing database...")
    run_command(
        f'{python_cmd} -c "from models.database import init_db; init_db()"',
        "Initializing database",
    )

    # Final instructions
    print("\n" + "=" * 60)
    print("Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print(f"1. Activate the virtual environment:")
    print(f"   {activate_cmd}")
    print("\n2. Run the application:")
    print("   python app.py")
    print("\n3. Access the API at:")
    print("   http://localhost:5000")
    print("\n4. Upload a contract:")
    print("   Use the sample contract in sample_contracts/service_agreement.txt")
    print("\n5. Run tests:")
    print("   pytest tests/")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
