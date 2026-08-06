# The hull shared by the test configurations: what any machine needs to
# evaluate to a toplevel, none of it ever used.
{ ... }:
{
  nixpkgs.hostPlatform = "x86_64-linux";
  boot.loader.grub.enable = false;
  fileSystems."/" = {
    device = "/dev/null";
    fsType = "ext4";
  };
  system.stateVersion = "26.05";
}
