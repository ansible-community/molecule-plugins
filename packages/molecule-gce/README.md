# Molecule GCE Plugin
[![PyPI Package][]][1] [![image][]][2] [![Python Black Code Style][]][3] [![Ansible Code of Conduct][]][4] [![Ansible mailing lists][]][5] [![Repository License -->][]][6]

  [PyPI Package]: https://badge.fury.io/py/molecule-gce.svg
  [1]: https://badge.fury.io/py/molecule-gce
  [image]: https://zuul-ci.org/gated.svg
  [2]: https://dashboard.zuul.ansible.com/t/ansible/builds?project=ansible-community/molecule-gce
  [Python Black Code Style]: https://img.shields.io/badge/code%20style-black-000000.svg
  [3]: https://github.com/python/black
  [Ansible Code of Conduct]: https://img.shields.io/badge/Code%20of%20Conduct-Ansible-silver.svg
  [4]: https://docs.ansible.com/ansible/latest/community/code_of_conduct.html
  [Ansible mailing lists]: https://img.shields.io/badge/Mailing%20lists-Ansible-orange.svg
  [5]: https://docs.ansible.com/ansible/latest/community/communication.html#mailing-list-information
  [Repository License -->]: https://img.shields.io/badge/license-MIT-brightgreen.svg
  [6]: LICENSE

Molecule GCE is designed to allow use Google Cloud Engine for
provisioning test resources.

Please note that this driver is currently in its early stage of development.

This plugin requires google.cloud and community.crypto collections to be present:
```
ansible-galaxy collection install google.cloud
ansible-galaxy collection install community.crypto
```

# Installation and Usage

Install molecule-gce :
```
pip install molecule-gce
```

Create a new role with molecule using the GCE driver:
```
molecule init role <role_name> -d gce
```

Configure `<role_name>/molecule/default/molecule.yml` with required parameters:

```yaml
dependency:
  name: galaxy
driver:
  name: gce
  project_id: my-google-cloud-platform-project-id  # if not set, will default to env GCE_PROJECT_ID
  region: us-central1  # REQUIRED
  network_name: my-vpc  # specify if other than default
  subnetwork_name: my-subnet  # specify if other than default
  vpc_host_project: null  # if you use a shared vpc, set here the vpc host project. In that case, your GCP user needs the necessary permissions in the host project, see https://cloud.google.com/vpc/docs/shared-vpc#iam_in_shared_vpc
  auth_kind: serviceaccount  # set to machineaccount or serviceaccount or application - if set to null will read env GCP_AUTH_KIND
  service_account_email: null  # set to an email associated with the project - if set to null, will default to GCP_SERVICE_ACCOUNT_EMAIL. Should not be set if using auth_kind serviceaccount.
  service_account_file: /path/to/gce-sa.json  # set to the path to the JSON credentials file - if set to null, will default to env GCP_SERVICE_ACCOUNT_FILE
  scopes:
    - "https://www.googleapis.com/auth/compute"  # will default to env GCP_SCOPES, https://www.googleapis.com/auth/compute is the minimum required scope.
  external_access: false  # chose whether to create a public IP for the VM or not - default is private IP only
  instance_os_type: linux  # Either windows or linux. Will be considered linux by default. You can NOT mix Windows and Linux VMs in the same scenario.
platforms:
  - name: ubuntu-instance-created-by-molecule  #  REQUIRED: this will be your VM name
    zone: us-central1-a  # Example: us-west1-b. Will default to zone b of region defined in driver (some regions do not have a zone-a)
    machine_type: n1-standard-1  # If not specified, will default to n1-standard-1
    preemptible: false  # If not specified, will default to false. Preemptible instances have no SLA, in case of resource shortage in the zone they might get destroyed (or not be created) without warning, and will always be terminated after 24 hours. But they cost less and will mitigate the financial consequences of a PAYG licenced VM that would be forgotten.
    image: 'projects/ubuntu-os-cloud/global/images/family/ubuntu-1604-lts'  # Points to an image, you can get a list of available images with command 'gcloud compute images list'.
       # The expected format of this string is projects/<project>/global/images/family/<family-name>
       # (see https://googlecloudplatform.github.io/compute-image-tools/daisy-automating-image-creation.html)
       #  Wille default to debian-10 image for os_type Linux, Windows 2019 for os_type Windows
  - name: debian-instance-created-by-molecule
    zone: us-central1-a
    machine_type: n1-standard-2
    image: 'projects/debian-cloud/global/images/family/debian-10'
  - name: n1-standard1-debian10-in-region-b


provisioner:
  name: ansible
verifier:
  name: ansible
```

# Get Involved

* Join us in the ``#ansible-molecule`` channel on [Freenode](https://freenode.net).
* Join the discussion in [molecule-users Forum](https://groups.google.com/forum/#!forum/molecule-users).
* Join the community working group by checking the [wiki](https://github.com/ansible/community/wiki/Molecule).
* Want to know about releases, subscribe to [ansible-announce list](https://groups.google.com/group/ansible-announce).
* For the full list of Ansible email Lists, IRC channels see the
  [communication page](https://docs.ansible.com/ansible/latest/community/communication.html).

# License

The [MIT](https://github.com/ansible-community/molecule-gce/blob/main/LICENSE) License.

The logo is licensed under the [Creative Commons NoDerivatives 4.0 License](https://creativecommons.org/licenses/by-nd/4.0/).

If you have some other use in mind, contact us.
