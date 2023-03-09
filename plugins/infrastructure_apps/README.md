# resoto-plugin-infrastructure-apps
Resoto infrastructure apps plugin

## Usage

In `resh` execute

```
> config edit resoto.worker
```

and find the following section

```
infrastructure:
  # Enable plugin?
  enabled: true
  # Infrastructure Apps to run
  apps:
    cleanup_untagged:
      # Enable infrastructure app?
      enabled: true
      # Which action to run this app on
      on_event: 'cleanup_plan'
      # Description of the app
      description: 'Cleanup untagged resources'
      # The infrastructure app template
      template: |
        {%- set tags_part = 'not(has_key(tags, ["' + '", "'.join(config["tags"]) + '"]))' %}
        {%- set kinds_part = 'is(["' + '", "'.join(config["kinds"]) + '"])' %}
        {%- set account_parts = [] %}
        {%- set default_age = config["default"]["age"]|default("2h") %}
        {%- for cloud_id, account in config["accounts"].items() %}
            {%- for account_id, account_data in account.items() %}
                {%- set age = account_data.get("age", default_age) %}
                {%- set account_part = '(/ancestors.cloud.id == "' ~ cloud_id ~ '" and /ancestors.account.id == "' ~ account_id ~ '" and age > ' ~ age ~ ')' %}
                {%- do account_parts.append(account_part) %}
            {%- endfor %}
        {%- endfor %}
        {%- set accounts_part = "(" + " or ".join(account_parts) + ")" %}
        {%- set exclusion_part = "/metadata.protected == false and /metadata.phantom == false and /metadata.cleaned == false" %}
        {%- set required_tags = ", ".join(config["tags"]) %}
        {%- set reason = "Missing one or more of required tags " ~ required_tags ~ " and age more than threshold" %}
        {%- set cleanup_search = 'search ' ~ exclusion_part ~ ' and ' ~ kinds_part ~ ' and ' ~ tags_part ~ ' and ' ~ accounts_part ~ ' | clean "' ~ reason ~ '"' %}
        {{ cleanup_search }}
      # Configuration for the app
      config:
        default:
          age: '2h'
        tags:
          - 'owner'
          - 'expiration'
        kinds:
          - 'aws_ec2_instance'
          - 'aws_ec2_volume'
          - 'aws_vpc'
          - 'aws_cloudformation_stack'
          - 'aws_elb'
          - 'aws_alb'
          - 'aws_alb_target_group'
          - 'aws_eks_cluster'
          - 'aws_eks_nodegroup'
        accounts:
          aws:
            '625596817853':
              name: 'someengineering-development'
              age: '7d'
            '752466027617':
              name: 'someengineering-sandbox'
```
