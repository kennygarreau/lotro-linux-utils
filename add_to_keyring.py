# you should run this once per account to add to your keyring
import keyring

def run():
    service = "lotro-multibox"

    username = "Frodo"
    password = "mypass123"

    print(keyring.get_keyring())
    #keyring.set_password(service, username, password)

if __name__ == "__main__":
    run()