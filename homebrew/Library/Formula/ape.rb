require 'formula'

class Ape < Formula
  homepage 'http://www.ape-project.org/'
  url 'https://github.com/APE-Project/APE_Server/tarball/v1.1.0'
  md5 '8e2d75bc558aa908e18c6765fc65eb53'

  def install
    system "./build.sh"
    system "make", "install", "prefix=#{prefix}"
  end
end
