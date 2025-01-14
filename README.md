# molecule-plugins

This repository contains the following molecule plugins:

- azure
- containers
- docker
- ec2
- gce
- openstack
- podman
- vagrant

Installing `molecule-plugins` does not install dependencies specific to each,
plugin. To install these you need to install the extras for each plugin, like
`pip3 install 'molecule-plugins[azure]'`.

Before installing these plugins be sure that you uninstall their old standalone
packages, like `pip3 uninstall molecule-azure`. If you fail to do so, you will
end-up with a broken setup, as multiple plugins will have the same entry points,
registered.

## Creating new releases

The `release.yml` workflow generates the wheel and uploads the release to PyPI.
Here are the steps you need to kick that process off:

1. Review the commit logs and decide on the next version.
   - Breaking changes should increment to a new major version.
   - New features should increment to a new minor version.
   - Bug fixes and small changes should increment to a new patch version.

2. Create a new tag and push it to the repo.

   ```bash
   git tag -s <NEW_VERSION> -m "Tag message"
   git push --tags upstream
   ```

   > It is possible to create lightweight tags using `git tag <NEW_VERSION>` but signed tags are preferred.

3. Publish the release with either the GitHub CLI or in a browser.
   See the [GitHub documentation about managing releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository).
4. Check the [release workflow](https://github.com/ansible-community/molecule-plugins/actions/workflows/release.yml) runs successfully.
5. Verify the new version is available from the [molecule-plugins](https://pypi.org/project/molecule-plugins/) page on PyPI.
