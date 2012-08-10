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

package org.keyczar.exceptions;

import org.keyczar.i18n.Messages;

/**
 * The signature attached to a given ciphertext or other Keyczar output doesn't
 * properly correspond to it.
 *
 * @author steveweis@gmail.com (Steve Weis)
 *
 */
public class InvalidSignatureException extends KeyczarException {
  private static final long serialVersionUID = -9209043556761224393L;

  public InvalidSignatureException() {
    super(Messages.getString("InvalidSignatureException"));
  }
}