require 'formula'

class Whohas < Formula
  url 'http://www.philippwesche.org/200811/whohas/whohas-0.29.tar.gz'
  homepage 'http://www.philippwesche.org/200811/whohas/intro.html'
  md5 'd12590e7d2c3c123b4cfb5b93ed4e902'

  depends_on 'LWP::UserAgent' => :perl

  def install
    bin.install 'program/whohas'
    man1.install 'usr/share/man/man1/whohas.1'
    (share+'whohas').install 'intro.txt'
  end
end
