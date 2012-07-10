require 'formula'

class Libcuefile < Formula
  homepage 'http://www.musepack.net/'
  url 'http://files.musepack.net/source/libcuefile_r475.tar.gz'
  md5 '1a6ac52e1080fd54f0f59372345f1e4e'
  version 'r475'

  depends_on 'cmake' => :build

  def install
    system "cmake", ".", *std_cmake_args
    system "make install"
    include.install 'include/cuetools/'
  end
end
