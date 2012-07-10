require 'formula'

class Voldemort < Formula
  homepage 'http://project-voldemort.com/'
  url 'https://github.com/downloads/voldemort/voldemort/voldemort-0.90.1.tar.gz'
  sha1 '8a8d33e3a5904f3aeea66bc0503fb12e449e0969'

  def install
    system "ant"
    libexec.install %w(bin lib dist contrib)
    libexec.install "config" => "config-examples"
    (libexec+"config").mkpath

    # Write shim scripts for all utilities
    Dir["#{libexec}/bin/*.sh"].each do |p|
      script = File.basename(p)
      (bin+script).write <<-EOS.undent
        #!/bin/bash
        exec #{p} "$@"
      EOS
    end
  end

  def caveats; <<-EOS.undent
    You will need to set VOLDEMORT_HOME to:
      #{libexec}

    Config files should be placed in:
      #{libexec}/config
    or you can set VOL_CONF_DIR to a more reasonable path.
    EOS
  end
end
