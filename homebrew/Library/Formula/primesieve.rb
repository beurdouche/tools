require 'formula'

class Primesieve < Formula
  homepage 'http://code.google.com/p/primesieve/'
  url 'http://primesieve.googlecode.com/files/primesieve-3.8-src.zip'
  sha1 'ada0024ed13be6b43eb70f7c794161e289e73d5d'

  def install
    system "make", "bin", "lib",
                   "SHARED=yes",
                   "CXX=#{ENV.cxx}",
                   "CXXFLAGS=#{ENV.cxxflags}"
    system "make", "PREFIX=#{prefix}", "install"
  end

  def test
    system "#{bin}/primesieve", "-v"
  end
end
