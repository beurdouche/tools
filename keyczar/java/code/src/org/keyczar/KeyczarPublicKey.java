/*
 * Copyright 2008 Google Inc.
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


/**
 * A placeholder public key class. We would use an interface, except want public
 * keys to be instances of KeyczarKeys
 *
 * @author steveweis@gmail.com (Steve Weis)
 *
 */
public abstract class KeyczarPublicKey extends KeyczarKey {
  protected KeyczarPublicKey(int size) {
    super(size);
  }
}