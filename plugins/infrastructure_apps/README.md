# resoto-plugin-infrastructure-apps
Resoto infrastructure apps plugin.

This plugin renders a template and takes a config as input to the template. The template is rendered for each app in the config and the rendered template is executed when the specified event occurs.
Each line of template output is executed as a separate Resoto command. See the example below.

## Example Usage

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

When rendered the app above would generate a command that looks like this
```
search /metadata.protected == false and /metadata.phantom == false and /metadata.cleaned == false and is(["aws_ec2_instance", "aws_ec2_volume", "aws_vpc", "aws_cloudformation_stack", "aws_elb", "aws_alb", "aws_alb_target_group", "aws_eks_cluster", "aws_eks_nodegroup"]) and not(has_key(tags, ["owner", "expiration"])) and ((/ancestors.cloud.id == "aws" and /ancestors.account.id == "625596817853" and age > 7d) or (/ancestors.cloud.id == "aws" and /ancestors.account.id == "752466027617" and age > 2h)) | clean "Missing one or more of required tags owner, expiration and age more than threshold"
```

An app can generate multiple lines of commands which will get executed one by one.

## Executing searches
Within the app template you can call the `search()` function which allows the template to search in the Resoto infrastructure graph.

Example
```
    graph_search:
      # Enable infrastructure app?
      enabled: false
      # Which action to run this app on
      on_event: 'post_generate_metrics'
      # Description of the app
      description: 'Search for stuff'
      # The infrastructure app template
      template: 'echo Account {% for account in search("is(aws_account) and /reported.name ~ someengineering") %}{{ account[''reported''][''name''] }}{% if not loop.last %}, {% endif %}{% endfor %}'
      # Configuration for the app
      config:
        foo: 'bar'
```

The above app would generate the following command
```
echo Account someengineering-development, someengineering-sandbox, someengineering-production
```
