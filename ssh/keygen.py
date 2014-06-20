import os
from Crypto.PublicKey import RSA

def generate_key():
    return RSA.generate(2048)

def check_key_already_generated():
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"id_rsa"), 'r') as private_key:
        if private_key.read(11) == "UNGENERATED":
            return False
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"id_rsa.pub"), 'r') as public_key:
        if public_key.read(11) == "UNGENERATED":
            return False
    return True

def create_keypair():
    key = generate_key()
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"id_rsa"), 'w') as content_file:
        content_file.write(key.exportKey('PEM'))

    pubkey = key.publickey()
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)),"id_rsa.pub"), 'w') as content_file:
        content_file.write(pubkey.exportKey('OpenSSH')+" core")
        
if __name__ == "__main__":
    create_keypair()
