from plugin-installer import run as install_plugins
from add-to-keyring import run as add_credentials
from update-music-db import run as update_music
from lotro-multibox import run as start_multibox

def menu():
    while True:
        print("\n=== LOTRO Utilities ===")
        print("1) Start multibox session")
        print("2) Install plugins")
        print("3) Add credentials to keyring")
        print("4) Refresh music database")
        print("5) Exit")

        choice = input("Select an option: ")

        if choice == "1":
            start_multibox()
        elif choice == "2":
            install_plugins()
        elif choice == "3":
            add_credentials()
        elif choice == "4":
            update_music()
        elif choice == "5":
            break
        else:
            print("Invalid selection — try again.")

if __name__ == "__main__":
    menu()
