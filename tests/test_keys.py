#!/usr/bin/env python

"""
<Program Name>
  test_keys.py

<Author>
  Vladimir Diaz

<Started>
  October 10, 2013.

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Test cases for test_keys.py.
"""

# Help with Python 3 compatibility, where the print statement is a function, an
# implicit relative import is invalid, and the '/' operator performs true
# division.  Example:  print 'hello world' raises a 'SyntaxError' exception.
from __future__ import print_function
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import unittest
import logging


import securesystemslib.exceptions
import securesystemslib.formats
import securesystemslib.keys
import securesystemslib.ecdsa_keys

logger = logging.getLogger('securesystemslib_test_keys')

KEYS = securesystemslib.keys
FORMAT_ERROR_MSG = 'securesystemslib.exceptions.FormatError was raised!' + \
  '  Check object\'s format.'
DATA = 'SOME DATA REQUIRING AUTHENTICITY.'



class TestKeys(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.rsakey_dict = KEYS.generate_rsa_key()
    cls.ed25519key_dict = KEYS.generate_ed25519_key()
    cls.ecdsakey_dict = KEYS.generate_ecdsa_key()

  def test_generate_rsa_key(self):
    default_rsa_library = KEYS._RSA_CRYPTO_LIBRARY
    for rsa_crypto_library in ['pycrypto', 'pyca-cryptography']:
      KEYS._RSA_CRYPTO_LIBRARY = rsa_crypto_library

      _rsakey_dict = KEYS.generate_rsa_key()

      # Check if the format of the object returned by generate() corresponds
      # to RSAKEY_SCHEMA format.
      self.assertEqual(None, securesystemslib.formats.RSAKEY_SCHEMA.check_match(_rsakey_dict),
                       FORMAT_ERROR_MSG)

      # Passing a bit value that is <2048 to generate() - should raise
      # 'securesystemslib.exceptions.FormatError'.
      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.generate_rsa_key, 555)

      # Passing a string instead of integer for a bit value.
      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.generate_rsa_key, 'bits')

      # NOTE if random bit value >=2048 (not 4096) is passed generate(bits)
      # does not raise any errors and returns a valid key.
      self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(KEYS.generate_rsa_key(2048)))
      self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(KEYS.generate_rsa_key(4096)))

    # Reset to originally set RSA crypto library.
    KEYS._RSA_CRYPTO_LIBRARY = default_rsa_library



  def test_generate_ecdsa_key(self):
      _ecdsakey_dict = KEYS.generate_ecdsa_key()

      # Check if the format of the object returned by generate_ecdsa_key()
      # corresponds to ECDSAKEY_SCHEMA format.
      self.assertEqual(None,
        securesystemslib.formats.ECDSAKEY_SCHEMA.check_match(_ecdsakey_dict),
        FORMAT_ERROR_MSG)

      # Passing an invalid algorithm to generate() should raise
      # 'securesystemslib.exceptions.FormatError'.
      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.generate_rsa_key, 'bad_algorithm')

      # Passing a string instead of integer for a bit value.
      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.generate_rsa_key, 123)



  def test_format_keyval_to_metadata(self):
    keyvalue = self.rsakey_dict['keyval']
    keytype = self.rsakey_dict['keytype']
    scheme = self.rsakey_dict['scheme']

    key_meta = KEYS.format_keyval_to_metadata(keytype, scheme, keyvalue)

    # Check if the format of the object returned by this function corresponds
    # to KEY_SCHEMA format.
    self.assertEqual(None,
                     securesystemslib.formats.KEY_SCHEMA.check_match(key_meta),
                     FORMAT_ERROR_MSG)
    key_meta = KEYS.format_keyval_to_metadata(keytype, scheme, keyvalue, private=True)

    # Check if the format of the object returned by this function corresponds
    # to KEY_SCHEMA format.
    self.assertEqual(None, securesystemslib.formats.KEY_SCHEMA.check_match(key_meta),
                     FORMAT_ERROR_MSG)

    # Supplying a 'bad' keyvalue.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.format_keyval_to_metadata,
                      'bad_keytype', scheme, keyvalue, private=True)

    # Test for missing 'public' entry.
    public = keyvalue['public']
    del keyvalue['public']
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.format_keyval_to_metadata,
                      keytype, scheme, keyvalue)
    keyvalue['public'] = public

    # Test for missing 'private' entry.
    private = keyvalue['private']
    del keyvalue['private']
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.format_keyval_to_metadata,
                      keytype, scheme, keyvalue, private=True)
    keyvalue['private'] = private



  def test_import_rsakey_from_public_pem(self):
    pem = self.rsakey_dict['keyval']['public']
    rsa_key = KEYS.import_rsakey_from_public_pem(pem)

    # Check if the format of the object returned by this function corresponds
    # to 'securesystemslib.formats.RSAKEY_SCHEMA' format.
    self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(rsa_key))

    # Verify whitespace is stripped.
    self.assertEqual(rsa_key, KEYS.import_rsakey_from_public_pem(pem + '\n'))

    # Supplying a 'bad_pem' argument.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem, 'bad_pem')

    # Supplying an improperly formatted PEM.
    # Strip the PEM header and footer.
    pem_header = '-----BEGIN PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem,
                      pem[len(pem_header):])

    pem_footer = '-----END PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem,
                      pem[:-len(pem_footer)])



  def test_format_metadata_to_key(self):
    # Reconfiguring rsakey_dict to conform to KEY_SCHEMA
    # i.e. {keytype: 'rsa', keyval: {public: pub_key, private: priv_key}}
    keyid = self.rsakey_dict['keyid']
    del self.rsakey_dict['keyid']

    rsakey_dict_from_meta, junk = KEYS.format_metadata_to_key(self.rsakey_dict)

    # Check if the format of the object returned by this function corresponds
    # to RSAKEY_SCHEMA format.
    self.assertEqual(None,
           securesystemslib.formats.RSAKEY_SCHEMA.check_match(rsakey_dict_from_meta),
           FORMAT_ERROR_MSG)

    self.assertEqual(None,
           securesystemslib.formats.KEY_SCHEMA.check_match(rsakey_dict_from_meta),
           FORMAT_ERROR_MSG)

    self.rsakey_dict['keyid'] = keyid

    # Supplying a wrong number of arguments.
    self.assertRaises(TypeError, KEYS.format_metadata_to_key)
    args = (self.rsakey_dict, self.rsakey_dict)
    self.assertRaises(TypeError, KEYS.format_metadata_to_key, *args)

    # Supplying a malformed argument to the function - should get FormatError
    keyval = self.rsakey_dict['keyval']
    del self.rsakey_dict['keyval']
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.format_metadata_to_key,
                      self.rsakey_dict)
    self.rsakey_dict['keyval'] = keyval



  def test_helper_get_keyid(self):
    keytype = self.rsakey_dict['keytype']
    keyvalue = self.rsakey_dict['keyval']
    scheme = self.rsakey_dict['scheme']

    # Check format of 'keytype'.
    self.assertEqual(None,
                     securesystemslib.formats.KEYTYPE_SCHEMA.check_match(keytype),
                     FORMAT_ERROR_MSG)

    # Check format of 'keyvalue'.
    self.assertEqual(None,
                     securesystemslib.formats.KEYVAL_SCHEMA.check_match(keyvalue),
                     FORMAT_ERROR_MSG)

    # Check format of 'scheme'.
    self.assertEqual(None,
                     securesystemslib.formats.RSA_SIG_SCHEMA.check_match(scheme),
                     FORMAT_ERROR_MSG)

    keyid = KEYS._get_keyid(keytype, scheme, keyvalue)

    # Check format of 'keyid' - the output of '_get_keyid()' function.
    self.assertEqual(None,
                     securesystemslib.formats.KEYID_SCHEMA.check_match(keyid),
                     FORMAT_ERROR_MSG)


  def test_create_signature(self):
    default_rsa_library = KEYS._RSA_CRYPTO_LIBRARY
    for rsa_crypto_library in ['pycrypto', 'pyca-cryptography']:
      KEYS._RSA_CRYPTO_LIBRARY = rsa_crypto_library

      # Creating a signature for 'DATA'.
      rsa_signature = KEYS.create_signature(self.rsakey_dict, DATA)
      ed25519_signature = KEYS.create_signature(self.ed25519key_dict, DATA)

      # Check format of output.
      self.assertEqual(None,
                       securesystemslib.formats.SIGNATURE_SCHEMA.check_match(rsa_signature),
                       FORMAT_ERROR_MSG)
      self.assertEqual(None,
                       securesystemslib.formats.SIGNATURE_SCHEMA.check_match(ed25519_signature),
                       FORMAT_ERROR_MSG)

      # Test for invalid signature scheme.
      args = (self.rsakey_dict, DATA)

      valid_scheme = self.rsakey_dict['scheme']
      self.rsakey_dict['scheme'] = 'invalid_scheme'
      self.assertRaises(securesystemslib.exceptions.UnsupportedAlgorithmError,
          KEYS.create_signature, *args)
      self.rsakey_dict['scheme'] = valid_scheme

      # Removing private key from 'rsakey_dict' - should raise a TypeError.
      private = self.rsakey_dict['keyval']['private']
      self.rsakey_dict['keyval']['private'] = ''

      self.assertRaises(ValueError, KEYS.create_signature, *args)

      # Supplying an incorrect number of arguments.
      self.assertRaises(TypeError, KEYS.create_signature)
      self.rsakey_dict['keyval']['private'] = private

    KEYS._RSA_CRYPTO_LIBRARY = default_rsa_library

    # Test generation of ECDSA signatures.
    default_ecdsa_library = KEYS._ECDSA_CRYPTO_LIBRARY
    for ecdsa_crypto_library in ['pyca-cryptography']:
      KEYS._ECDSA_CRYPTO_LIBRARY = ecdsa_crypto_library

      # Creating a signature for 'DATA'.
      ecdsa_signature = KEYS.create_signature(self.ecdsakey_dict, DATA)
      ecdsa_signature = KEYS.create_signature(self.ecdsakey_dict, DATA)

      # Check format of output.
      self.assertEqual(None,
                       securesystemslib.formats.SIGNATURE_SCHEMA.check_match(ecdsa_signature),
                       FORMAT_ERROR_MSG)
      self.assertEqual(None,
                       securesystemslib.formats.SIGNATURE_SCHEMA.check_match(ecdsa_signature),
                       FORMAT_ERROR_MSG)

      # Removing private key from 'ecdsakey_dict' - should raise a TypeError.
      private = self.ecdsakey_dict['keyval']['private']
      self.ecdsakey_dict['keyval']['private'] = ''

      args = (self.ecdsakey_dict, DATA)
      self.assertRaises(ValueError, KEYS.create_signature, *args)

      # Supplying an incorrect number of arguments.
      self.assertRaises(TypeError, KEYS.create_signature)
      self.ecdsakey_dict['keyval']['private'] = private




  def test_verify_signature(self):
    default_rsa_library = KEYS._RSA_CRYPTO_LIBRARY
    default_available_libraries = KEYS._available_crypto_libraries

    for crypto_library in ['pycrypto', 'pyca-cryptography']:
      KEYS._RSA_CRYPTO_LIBRARY = crypto_library
      KEYS._ECDSA_CRYPTO_LIBRARY = crypto_library

      # Creating a signature of 'DATA' to be verified.
      rsa_signature = KEYS.create_signature(self.rsakey_dict, DATA)
      ed25519_signature = KEYS.create_signature(self.ed25519key_dict, DATA)
      ecdsa_signature = None

      if crypto_library == 'pyca-cryptography':
        ecdsa_signature = KEYS.create_signature(self.ecdsakey_dict, DATA)

      else:
        logger.debug('Skip creation of ECDSA signature using ' + repr(crypto_library))

      # Verifying the 'signature' of 'DATA'.
      verified = KEYS.verify_signature(self.rsakey_dict, rsa_signature, DATA)
      self.assertTrue(verified, "Incorrect signature.")

      # Verifying the 'ed25519_signature' of 'DATA'.
      verified = KEYS.verify_signature(self.ed25519key_dict, ed25519_signature,
                                       DATA)
      self.assertTrue(verified, "Incorrect signature.")

      # Verify that an invalid ed25519 signature scheme is rejected.
      valid_scheme = self.ed25519key_dict['scheme']
      self.ed25519key_dict['scheme'] = 'invalid_scheme'
      self.assertRaises(securesystemslib.exceptions.UnsupportedAlgorithmError,
          KEYS.verify_signature, self.ed25519key_dict, ed25519_signature, DATA)
      self.ed25519key_dict['scheme'] = valid_scheme

      # Verifying the 'ecdsa_sigature' of 'DATA'.
      if ecdsa_signature:
        verified = KEYS.verify_signature(self.ecdsakey_dict, ecdsa_signature, DATA)
        self.assertTrue(verified, "Incorrect signature.")

        # Verifying the 'ecdsa_signature' of 'DATA'.
        verified = KEYS.verify_signature(self.ecdsakey_dict, ecdsa_signature,
                                         DATA)
        self.assertTrue(verified, "Incorrect signature.")

        # Test for an invalid ecdsa signature scheme.
        valid_scheme = self.ecdsakey_dict['scheme']
        self.ecdsakey_dict['scheme'] = 'invalid_scheme'
        self.assertRaises(securesystemslib.exceptions.UnsupportedAlgorithmError,
            KEYS.verify_signature, self.ecdsakey_dict, ecdsa_signature, DATA)
        self.ecdsakey_dict['scheme'] = valid_scheme

      # Testing invalid signatures. Same signature is passed, with 'DATA' being
      # different than the original 'DATA' that was used in creating the
      # 'rsa_signature'. Function should return 'False'.

      # Modifying 'DATA'.
      _DATA = '1111' + DATA + '1111'

      # Verifying the 'signature' of modified '_DATA'.
      verified = KEYS.verify_signature(self.rsakey_dict, rsa_signature, _DATA)
      self.assertFalse(verified,
                       'Returned \'True\' on an incorrect signature.')

      verified = KEYS.verify_signature(self.ed25519key_dict, ed25519_signature, _DATA)
      self.assertFalse(verified,
                       'Returned \'True\' on an incorrect signature.')

      if ecdsa_signature:
        verified = KEYS.verify_signature(self.ecdsakey_dict, ecdsa_signature, _DATA)
        self.assertFalse(verified,
                         'Returned \'True\' on an incorrect signature.')

      # Modifying 'rsakey_dict' to pass an incorrect scheme since only
      # 'PyCrypto-PKCS#1 PSS' is accepted.
      valid_scheme = self.rsakey_dict['scheme']
      self.rsakey_dict['scheme'] = 'Biff'

      args = (self.rsakey_dict, rsa_signature, DATA)
      self.assertRaises(securesystemslib.exceptions.UnsupportedAlgorithmError,
          KEYS.verify_signature, *args)

      # Restore
      self.rsakey_dict['scheme'] = valid_scheme

      # Passing incorrect number of arguments.
      self.assertRaises(TypeError, KEYS.verify_signature)

      # Verify that the pure python 'ed25519' base case (triggered if 'pynacl'
      # is unavailable) is executed in securesystemslib.keys.verify_signature().
      KEYS._ED25519_CRYPTO_LIBRARY = 'invalid'
      KEYS._available_crypto_libraries = ['invalid']
      verified = KEYS.verify_signature(self.ed25519key_dict, ed25519_signature, DATA)
      self.assertTrue(verified, "Incorrect signature.")

      # Reset to the expected available crypto libraries.
      KEYS._ED25519_CRYPTO_LIBRARY = 'pynacl'
      KEYS._available_crypto_libraries = default_available_libraries

    KEYS._RSA_CRYPTO_LIBRARY = default_rsa_library



  def test_create_rsa_encrypted_pem(self):
    default_rsa_library = KEYS._RSA_CRYPTO_LIBRARY
    for rsa_crypto_library in ['pycrypto', 'pyca-cryptography']:
      KEYS._RSA_CRYPTO_LIBRARY = rsa_crypto_library

      # Test valid arguments.
      private = self.rsakey_dict['keyval']['private']
      passphrase = 'secret'
      scheme = 'rsassa-pss-sha256'
      encrypted_pem = KEYS.create_rsa_encrypted_pem(private, passphrase)
      self.assertTrue(securesystemslib.formats.PEMRSA_SCHEMA.matches(encrypted_pem))

      # Try to import the encrypted PEM file.
      rsakey = KEYS.import_rsakey_from_private_pem(encrypted_pem, scheme, passphrase)
      self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(rsakey))

      # Test improperly formatted arguments.
      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.create_rsa_encrypted_pem,
                        8, passphrase)

      self.assertRaises(securesystemslib.exceptions.FormatError,
                        KEYS.create_rsa_encrypted_pem,
                        private, 8)

      # Test for missing required library.
      KEYS._RSA_CRYPTO_LIBRARY = 'invalid'
      self.assertRaises(securesystemslib.exceptions.UnsupportedLibraryError,
                        KEYS.create_rsa_encrypted_pem,
                        private, passphrase)
      KEYS._RSA_CRYPTO_LIBRARY = 'pycrypto'

    KEYS._RSA_CRYPTO_LIBRARY = default_rsa_library



  def test_import_rsakey_from_private_pem(self):
    # Try to import an rsakey from a valid PEM.
    private_pem = self.rsakey_dict['keyval']['private']

    private_rsakey = KEYS.import_rsakey_from_private_pem(private_pem)

    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_private_pem, 123)



  def test_import_rsakey_from_public_pem(self):
    # Try to import an rsakey from a public PEM.
    pem = self.rsakey_dict['keyval']['public']
    rsa_key = KEYS.import_rsakey_from_public_pem(pem)

    # Check if the format of the object returned by this function corresponds
    # to 'securesystemslib.formats.RSAKEY_SCHEMA' format.
    self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(rsa_key))

    # Verify whitespace is stripped.
    self.assertEqual(rsa_key, KEYS.import_rsakey_from_public_pem(pem + '\n'))

    # Supplying a 'bad_pem' argument.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                     KEYS.import_rsakey_from_public_pem, 'bad_pem')

    # Supplying an improperly formatted PEM.
    # Strip the PEM header and footer.
    pem_header = '-----BEGIN PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem,
                      pem[len(pem_header):])

    pem_footer = '-----END PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem,
                      pem[:-len(pem_footer)])

    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_public_pem, 123)



  def test_import_rsakey_from_pem(self):
    # Try to import an rsakey from a public PEM.
    public_pem = self.rsakey_dict['keyval']['public']
    private_pem = self.rsakey_dict['keyval']['private']
    public_rsakey = KEYS.import_rsakey_from_pem(public_pem)
    private_rsakey = KEYS.import_rsakey_from_pem(private_pem)

    # Check if the format of the object returned by this function corresponds
    # to 'securesystemslib.formats.RSAKEY_SCHEMA' format.
    self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(public_rsakey))
    self.assertTrue(securesystemslib.formats.RSAKEY_SCHEMA.matches(private_rsakey))

    # Verify whitespace is stripped.
    self.assertEqual(public_rsakey, KEYS.import_rsakey_from_pem(public_pem + '\n'))
    self.assertEqual(private_rsakey, KEYS.import_rsakey_from_pem(private_pem + '\n'))

    # Supplying a 'bad_pem' argument.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem, 'bad_pem')

    # Supplying an improperly formatted public PEM.
    # Strip the PEM header and footer.
    pem_header = '-----BEGIN PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem,
                      public_pem[len(pem_header):])

    pem_footer = '-----END PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem,
                      public_pem[:-len(pem_footer)])

    # Supplying an improperly formatted private PEM.
    # Strip the PEM header and footer.
    pem_header = '-----BEGIN PRIVATE KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem,
                      private_pem[len(pem_header):])

    pem_footer = '-----END PRIVATE KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem,
                      private_pem[:-len(pem_footer)])

    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_rsakey_from_pem, 123)



  def test_import_ecdsakey_from_private_pem(self):
    # Try to import an ecdsakey from a valid PEM.
    private_pem = self.ecdsakey_dict['keyval']['private']
    ecdsakey = KEYS.import_ecdsakey_from_private_pem(private_pem)

    # Test for an encrypted PEM.
    scheme = 'ecdsa-sha2-nistp256'
    encrypted_pem = \
      securesystemslib.ecdsa_keys.create_ecdsa_encrypted_pem(private_pem, 'password')
    private_ecdsakey = KEYS.import_ecdsakey_from_private_pem(encrypted_pem.decode('utf-8'),
        scheme, 'password')


    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_private_pem, 123)



  def test_import_ecdsakey_from_public_pem(self):
    # Try to import an ecdsakey from a public PEM.
    pem = self.ecdsakey_dict['keyval']['public']
    ecdsa_key = KEYS.import_ecdsakey_from_public_pem(pem)

    # Check if the format of the object returned by this function corresponds
    # to 'securesystemslib.formats.ECDSAKEY_SCHEMA' format.
    self.assertTrue(securesystemslib.formats.ECDSAKEY_SCHEMA.matches(ecdsa_key))

    # Verify whitespace is stripped.
    self.assertEqual(ecdsa_key, KEYS.import_ecdsakey_from_public_pem(pem + '\n'))

    # Supplying a 'bad_pem' argument.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                     KEYS.import_ecdsakey_from_public_pem, 'bad_pem')

    # Supplying an improperly formatted PEM.  Strip the PEM header and footer.
    pem_header = '-----BEGIN PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_public_pem,
                      pem[len(pem_header):])

    pem_footer = '-----END PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_public_pem,
                      pem[:-len(pem_footer)])

    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_public_pem, 123)



  def test_import_ecdsakey_from_pem(self):
    # Try to import an ecdsakey from a public PEM.
    public_pem = self.ecdsakey_dict['keyval']['public']
    private_pem = self.ecdsakey_dict['keyval']['private']
    public_ecdsakey = KEYS.import_ecdsakey_from_pem(public_pem)
    private_ecdsakey = KEYS.import_ecdsakey_from_pem(private_pem)

    # Check if the format of the object returned by this function corresponds
    # to 'securesystemslib.formats.ECDSAKEY_SCHEMA' format.
    self.assertTrue(securesystemslib.formats.ECDSAKEY_SCHEMA.matches(public_ecdsakey))
    self.assertTrue(securesystemslib.formats.ECDSAKEY_SCHEMA.matches(private_ecdsakey))

    # Verify whitespace is stripped.
    self.assertEqual(public_ecdsakey, KEYS.import_ecdsakey_from_pem(public_pem + '\n'))
    self.assertEqual(private_ecdsakey, KEYS.import_ecdsakey_from_pem(private_pem + '\n'))

    # Supplying a 'bad_pem' argument.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem, 'bad_pem')

    # Supplying an improperly formatted public PEM.  Strip the PEM header and
    # footer.
    pem_header = '-----BEGIN PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem,
                      public_pem[len(pem_header):])

    pem_footer = '-----END PUBLIC KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem,
                      public_pem[:-len(pem_footer)])

    # Supplying an improperly formatted private PEM.  Strip the PEM header and
    # footer.
    pem_header = '-----BEGIN EC PRIVATE KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem,
                      private_pem[len(pem_header):])

    pem_footer = '-----END EC PRIVATE KEY-----'
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem,
                      private_pem[:-len(pem_footer)])

    # Test for invalid arguments.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.import_ecdsakey_from_pem, 123)



  def test_decrypt_key(self):
    default_general_library = KEYS._GENERAL_CRYPTO_LIBRARY
    for general_crypto_library in ['pycrypto', 'pyca-cryptography']:
      KEYS._GENERAL_CRYPTO_LIBRARY = general_crypto_library

      # Test valid arguments.
      passphrase = 'secret'
      encrypted_key = KEYS.encrypt_key(self.rsakey_dict, passphrase)
      decrypted_key = KEYS.decrypt_key(encrypted_key, passphrase)

      self.assertTrue(securesystemslib.formats.ANYKEY_SCHEMA.matches(decrypted_key))

      # Test improperly formatted arguments.
      self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.decrypt_key,
                        8, passphrase)

      self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.decrypt_key,
                        encrypted_key, 8)

      # Test for missing required library.
      KEYS._GENERAL_CRYPTO_LIBRARY = 'invalid'
      self.assertRaises(securesystemslib.exceptions.UnsupportedLibraryError,
                        KEYS.decrypt_key,
                        encrypted_key, passphrase)
      KEYS._GENERAL_CRYPTO_LIBRARY = 'pycrypto'

    KEYS._GENERAL_CRYPTO_LIBRARY = default_general_library



  def test_extract_pem(self):
    # Normal case.
    private_pem = KEYS.extract_pem(self.rsakey_dict['keyval']['private'],
                                   private_pem=True)
    self.assertTrue(securesystemslib.formats.PEMRSA_SCHEMA.matches(private_pem))

    public_pem = KEYS.extract_pem(self.rsakey_dict['keyval']['public'],
                                   private_pem=False)
    self.assertTrue(securesystemslib.formats.PEMRSA_SCHEMA.matches(public_pem))

    # Test for an invalid PEM.
    pem_header = '-----BEGIN RSA PRIVATE KEY-----'
    pem_footer = '-----END RSA PRIVATE KEY-----'

    private_header_start = private_pem.index(pem_header)
    private_footer_start = private_pem.index(pem_footer, private_header_start + len(pem_header))

    private_missing_header = private_pem[private_header_start + len(pem_header):private_footer_start + len(pem_footer)]
    private_missing_footer = private_pem[private_header_start:private_footer_start]

    pem_header = '-----BEGIN PUBLIC KEY-----'
    pem_footer = '-----END PUBLIC KEY-----'

    public_header_start = public_pem.index(pem_header)
    public_footer_start = public_pem.index(pem_footer, public_header_start + len(pem_header))

    public_missing_header = public_pem[public_header_start + len(pem_header):public_footer_start + len(pem_footer)]
    public_missing_footer = public_pem[public_header_start:public_footer_start]

    self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.extract_pem,
                      'invalid_pem', private_pem=False)

    self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.extract_pem,
                      public_missing_header, private_pem=False)
    self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.extract_pem,
                      private_missing_header, private_pem=True)

    self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.extract_pem,
                      public_missing_footer, private_pem=False)

    self.assertRaises(securesystemslib.exceptions.FormatError, KEYS.extract_pem,
                      private_missing_footer, private_pem=True)




  def test_is_pem_public(self):
    # Test for a valid PEM string.
    public_pem = self.rsakey_dict['keyval']['public']
    self.assertTrue(KEYS.is_pem_public(public_pem))

    # Tesst for a valid non-public PEM string.
    private_pem = self.rsakey_dict['keyval']['private']
    self.assertFalse(KEYS.is_pem_public(private_pem))

    # Test for an invalid PEM string.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.is_pem_public, 123)



  def test_is_pem_private(self):
    # Test for a valid PEM string.
    private_pem = self.rsakey_dict['keyval']['private']
    private_pem_ec = self.ecdsakey_dict['keyval']['private']

    self.assertTrue(KEYS.is_pem_private(private_pem))
    self.assertTrue(KEYS.is_pem_private(private_pem_ec, 'ec'))

    # Test for a valid non-private PEM string.
    public_pem = self.rsakey_dict['keyval']['public']
    public_pem_ec = self.ecdsakey_dict['keyval']['public']
    self.assertFalse(KEYS.is_pem_private(public_pem))
    self.assertFalse(KEYS.is_pem_private(public_pem_ec, 'ec'))

    # Test for unsupported keytype.
    self.assertRaises(securesystemslib.exceptions.FormatError,
      KEYS.is_pem_private, private_pem, 'bad_keytype')

    # Test for an invalid PEM string.
    self.assertRaises(securesystemslib.exceptions.FormatError,
                      KEYS.is_pem_private, 123)



# Run the unit tests.
if __name__ == '__main__':
  unittest.main()
