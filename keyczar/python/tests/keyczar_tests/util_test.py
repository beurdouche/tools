#!/usr/bin/python
#
# Copyright 2011 LightKeeper LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#      http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Testcases to test behavior of Keyczar utils.

@author: rleftwich@lightkeeper.com (Robert Leftwich)
"""

import unittest
import base64
import StringIO
import random
import os

from keyczar import util

class Base64WSStreamingReadTest(unittest.TestCase):

  def __readStream(self, stream, size=-1):
    result = ''
    read_data = True
    while read_data != '':
      if size >= 0:
        read_data = stream.read(size)
      else:
        read_data = stream.read()
      if read_data:
        result += read_data
    return result

  def __testRead(self, input_data, expected_result):
    for size in [1, 5, 4096, 99999, -1]:
      stream = util.IncrementalBase64WSStreamReader(StringIO.StringIO(input_data))
      self.assertEquals(self.__readStream(stream, size), expected_result)

  def testNoPadRead(self):
    no_pad_data = 'Some inspired test datum'
    b64_data = base64.urlsafe_b64encode(no_pad_data)
    self.assertFalse(b64_data.endswith('='))
    self.__testRead(b64_data, no_pad_data)

  def testSinglePadRead(self):
    single_pad_data = 'Some inspired test data'
    b64_data = base64.urlsafe_b64encode(single_pad_data)
    self.assertFalse(b64_data.endswith('=='))
    self.assertTrue(b64_data.endswith('='))
    self.__testRead(b64_data, single_pad_data)
    self.__testRead(b64_data[:-1], single_pad_data)

  def testDoublePadRead(self):
    double_pad_data = 'All inspired test data'
    b64_data = base64.urlsafe_b64encode(double_pad_data)
    self.assertTrue(b64_data.endswith('=='))
    self.__testRead(b64_data, double_pad_data)
    self.__testRead(b64_data[:-1], double_pad_data)
    self.__testRead(b64_data[:-2], double_pad_data)

  def testSimulateDecrypter(self):
    enc_data = \
    'AJehaFGwoOrkzpDCnF1zqIi721eCOMYWRmLyRyn3hxyhh_mYwpnDN6jKN057gr5lz' \
            'APFYhq9zoDwFMaGMEipEl__ECOZGeaxWw'
    expected_result = util.Base64WSDecode(enc_data)
    stream = util.IncrementalBase64WSStreamReader(StringIO.StringIO(enc_data))
    result = stream.read(5)
    result += stream.read(15)
    read_data = True
    while read_data:
      read_data = stream.read(4096)
      result += read_data
    self.assertEquals(result, expected_result)

class Base64WSStreamingWriteTest(unittest.TestCase):

  def __testWrite(self, input_data):

    expected_result = base64.urlsafe_b64encode(input_data)
    while expected_result[-1] == '=':
      expected_result = expected_result[:-1]

    for size in [1, 5, 4096, random.randrange(1, 9999), -1]:
      output_stream = StringIO.StringIO()
      stream = util.IncrementalBase64WSStreamWriter(output_stream)
      i = 0
      if size >= 0:
        while (i * size) <= len(input_data):
          stream.write(input_data[i * size:(i + 1) * size])
          i += 1
      else:
        stream.write(input_data)
      stream.flush()
      self.assertEquals(output_stream.getvalue(), expected_result)

  def testNoPadWrite(self):
    no_pad_data = 'Some inspired test datum'
    b64_data = base64.urlsafe_b64encode(no_pad_data)
    self.assertFalse(b64_data.endswith('='))
    self.__testWrite(no_pad_data)

  def testSinglePadWrite(self):
    single_pad_data = 'Some inspired test data'
    b64_data = base64.urlsafe_b64encode(single_pad_data)
    self.assertFalse(b64_data.endswith('=='))
    self.assertTrue(b64_data.endswith('='))
    self.__testWrite(single_pad_data)

  def testDoublePadWrite(self):
    double_pad_data = 'All inspired test data'
    b64_data = base64.urlsafe_b64encode(double_pad_data)
    self.assertTrue(b64_data.endswith('=='))
    self.__testWrite(double_pad_data)

  def testRandomLongerWrite(self):
    random_input_data = os.urandom(random.randrange(
      util.DEFAULT_STREAM_BUFF_SIZE * 2 + 1,
      50000))
    self.__testWrite(random_input_data)

def suite():
  alltests = unittest.TestSuite(
    [unittest.TestLoader().loadTestsFromTestCase(Base64WSStreamingReadTest),
     unittest.TestLoader().loadTestsFromTestCase(Base64WSStreamingWriteTest),
    ])

  return alltests

if __name__ == "__main__":
  unittest.main(defaultTest='suite')
