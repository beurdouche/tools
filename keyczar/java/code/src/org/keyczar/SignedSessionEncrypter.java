/*
 * Copyright 2011 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.keyczar;

import static org.keyczar.util.Util.rand;

import org.keyczar.annotations.Experimental;
import org.keyczar.exceptions.KeyczarException;
import org.keyczar.interfaces.KeyType;
import org.keyczar.util.Base64Coder;

import java.util.concurrent.atomic.AtomicReference;

/**
 * A session based encryption strategy with signing.
 *
 * The usage pattern for this class is as follows.
 *
 * 1) Create a new instance using a RSA Encrypter and DSA Signer.
 * 2) Initialize session material which generates a AES session key and signing
 *    nonce. Returns RSA encrypted material.
 * 3) encrypt, which pulls the session material, encrypts the plaintext, using
 *    the session AES key.
 * 4) generate a signature based on the DSA key and attach the signature
 *    to the encrypted payload.
 *
 * This class is not thread safe (yet).
 *
 * @author normandl@google.com (David Norman)
 *
 */
@Experimental
public class SignedSessionEncrypter {
  private static final int NONCE_SIZE = 16;
  private final Encrypter encrypter;
  private final Signer signer;

  private AtomicReference<SessionMaterial> session =
      new AtomicReference<SessionMaterial>();

  public SignedSessionEncrypter(Encrypter encrypter, Signer signer) {
    this.encrypter = encrypter;
    this.signer = signer;
  }

  /**
   * Create a new session.
   *
   * @return Base64 encoded session material
   * @throws KeyczarException
   */
  public String newSession() throws KeyczarException {
    return this.newSession(DefaultKeyType.AES.getAcceptableSizes().get(0));
  }

  /**
   * Create a new session with an AES key of specified size.
   *
   * @param aesKeySize supported AES key size.
   * @return Base64 encoded session material.
   * @throws KeyczarException
   */
  public String newSession(int aesKeySize) throws KeyczarException {
	KeyType type = DefaultKeyType.AES;
	if (!type.isAcceptableSize(aesKeySize)) {
      throw new KeyczarException("Unsupported key size requested for session");
	}

    AesKey aesKey = AesKey.generate(aesKeySize);

    byte[] nonce = new byte[NONCE_SIZE];
    rand(nonce);

    String nonceString = Base64Coder.encodeWebSafe(nonce);

    session.set(new SessionMaterial(aesKey, nonceString));

    // encrypt session data in its entirety
    return encrypter.encrypt(session.get().toString());
  }

  /**
   * Encrypt and sign the plaintext.
   *
   * @param plainText string to encrypt.
   * @return encrypted payload with signing attached.
   * @throws KeyczarException
   */
  public byte[] encrypt(byte[] plainText) throws KeyczarException {
	if (null == session.get()) {
      throw new KeyczarException("Session not initialized.");
	}
	
    SessionMaterial material = session.get();
    ImportedKeyReader importedKeyReader = new ImportedKeyReader(material.getKey());
    Crypter symmetricCrypter = new Crypter(importedKeyReader);
    byte[] ciphertext = symmetricCrypter.encrypt(plainText);

    // encrypted nonce is not base 64 encoded for the signature, so decode before
    // using for hidden.
    return signer.attachedSign(ciphertext, Base64Coder.decodeWebSafe(material.getNonce()));
  }
}
