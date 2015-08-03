from __future__ import unicode_literals
import boto
import boto.ec2.elb
from boto.ec2.elb import HealthCheck
from boto.ec2.elb.attributes import (
    ConnectionSettingAttribute,
    ConnectionDrainingAttribute,
    AccessLogAttribute,
)
from boto.ec2.elb.policies import (
    Policies,
    AppCookieStickinessPolicy,
    LBCookieStickinessPolicy,
    OtherPolicy,
)
import sure  # noqa

from moto import mock_elb, mock_ec2


@mock_elb
def test_create_load_balancer():
    conn = boto.connect_elb()

    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    conn.create_load_balancer('my-lb', zones, ports)

    balancers = conn.get_all_load_balancers()
    balancer = balancers[0]
    balancer.name.should.equal("my-lb")
    set(balancer.availability_zones).should.equal(set(['us-east-1a', 'us-east-1b']))
    listener1 = balancer.listeners[0]
    listener1.load_balancer_port.should.equal(80)
    listener1.instance_port.should.equal(8080)
    listener1.protocol.should.equal("HTTP")
    listener2 = balancer.listeners[1]
    listener2.load_balancer_port.should.equal(443)
    listener2.instance_port.should.equal(8443)
    listener2.protocol.should.equal("TCP")


@mock_elb
def test_create_elb_in_multiple_region():
    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]

    west1_conn = boto.ec2.elb.connect_to_region("us-west-1")
    west1_conn.create_load_balancer('my-lb', zones, ports)

    west2_conn = boto.ec2.elb.connect_to_region("us-west-2")
    west2_conn.create_load_balancer('my-lb', zones, ports)

    list(west1_conn.get_all_load_balancers()).should.have.length_of(1)
    list(west2_conn.get_all_load_balancers()).should.have.length_of(1)

@mock_elb
def test_create_load_balancer_with_certificate():
    conn = boto.connect_elb()

    zones = ['us-east-1a']
    ports = [(443, 8443, 'https', 'arn:aws:iam:123456789012:server-certificate/test-cert')]
    conn.create_load_balancer('my-lb', zones, ports)

    balancers = conn.get_all_load_balancers()
    balancer = balancers[0]
    balancer.name.should.equal("my-lb")
    set(balancer.availability_zones).should.equal(set(['us-east-1a']))
    listener = balancer.listeners[0]
    listener.load_balancer_port.should.equal(443)
    listener.instance_port.should.equal(8443)
    listener.protocol.should.equal("HTTPS")
    listener.ssl_certificate_id.should.equal('arn:aws:iam:123456789012:server-certificate/test-cert')


@mock_elb
def test_add_listener():
    conn = boto.connect_elb()
    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http')]
    conn.create_load_balancer('my-lb', zones, ports)
    new_listener = (443, 8443, 'tcp')
    conn.create_load_balancer_listeners('my-lb', [new_listener])
    balancers = conn.get_all_load_balancers()
    balancer = balancers[0]
    listener1 = balancer.listeners[0]
    listener1.load_balancer_port.should.equal(80)
    listener1.instance_port.should.equal(8080)
    listener1.protocol.should.equal("HTTP")
    listener2 = balancer.listeners[1]
    listener2.load_balancer_port.should.equal(443)
    listener2.instance_port.should.equal(8443)
    listener2.protocol.should.equal("TCP")


@mock_elb
def test_delete_listener():
    conn = boto.connect_elb()

    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    conn.create_load_balancer('my-lb', zones, ports)
    conn.delete_load_balancer_listeners('my-lb', [443])
    balancers = conn.get_all_load_balancers()
    balancer = balancers[0]
    listener1 = balancer.listeners[0]
    listener1.load_balancer_port.should.equal(80)
    listener1.instance_port.should.equal(8080)
    listener1.protocol.should.equal("HTTP")
    balancer.listeners.should.have.length_of(1)


@mock_elb
def test_set_sslcertificate():
    conn = boto.connect_elb()

    zones = ['us-east-1a', 'us-east-1b']
    ports = [(443, 8443, 'tcp')]
    conn.create_load_balancer('my-lb', zones, ports)
    conn.set_lb_listener_SSL_certificate('my-lb', '443', 'arn:certificate')
    balancers = conn.get_all_load_balancers()
    balancer = balancers[0]
    listener1 = balancer.listeners[0]
    listener1.load_balancer_port.should.equal(443)
    listener1.instance_port.should.equal(8443)
    listener1.protocol.should.equal("TCP")
    listener1.ssl_certificate_id.should.equal("arn:certificate")


@mock_elb
def test_get_load_balancers_by_name():
    conn = boto.connect_elb()

    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    conn.create_load_balancer('my-lb1', zones, ports)
    conn.create_load_balancer('my-lb2', zones, ports)
    conn.create_load_balancer('my-lb3', zones, ports)

    conn.get_all_load_balancers().should.have.length_of(3)
    conn.get_all_load_balancers(load_balancer_names=['my-lb1']).should.have.length_of(1)
    conn.get_all_load_balancers(load_balancer_names=['my-lb1', 'my-lb2']).should.have.length_of(2)


@mock_elb
def test_delete_load_balancer():
    conn = boto.connect_elb()

    zones = ['us-east-1a']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    conn.create_load_balancer('my-lb', zones, ports)

    balancers = conn.get_all_load_balancers()
    balancers.should.have.length_of(1)

    conn.delete_load_balancer("my-lb")
    balancers = conn.get_all_load_balancers()
    balancers.should.have.length_of(0)


@mock_elb
def test_create_health_check():
    conn = boto.connect_elb()

    hc = HealthCheck(
        interval=20,
        healthy_threshold=3,
        unhealthy_threshold=5,
        target='HTTP:8080/health',
        timeout=23,
    )

    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    lb.configure_health_check(hc)

    balancer = conn.get_all_load_balancers()[0]
    health_check = balancer.health_check
    health_check.interval.should.equal(20)
    health_check.healthy_threshold.should.equal(3)
    health_check.unhealthy_threshold.should.equal(5)
    health_check.target.should.equal('HTTP:8080/health')
    health_check.timeout.should.equal(23)


@mock_ec2
@mock_elb
def test_register_instances():
    ec2_conn = boto.connect_ec2()
    reservation = ec2_conn.run_instances('ami-1234abcd', 2)
    instance_id1 = reservation.instances[0].id
    instance_id2 = reservation.instances[1].id

    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    lb.register_instances([instance_id1, instance_id2])

    balancer = conn.get_all_load_balancers()[0]
    instance_ids = [instance.id for instance in balancer.instances]
    set(instance_ids).should.equal(set([instance_id1, instance_id2]))


@mock_ec2
@mock_elb
def test_deregister_instances():
    ec2_conn = boto.connect_ec2()
    reservation = ec2_conn.run_instances('ami-1234abcd', 2)
    instance_id1 = reservation.instances[0].id
    instance_id2 = reservation.instances[1].id

    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    lb.register_instances([instance_id1, instance_id2])

    balancer = conn.get_all_load_balancers()[0]
    balancer.instances.should.have.length_of(2)
    balancer.deregister_instances([instance_id1])

    balancer.instances.should.have.length_of(1)
    balancer.instances[0].id.should.equal(instance_id2)


@mock_elb
def test_default_attributes():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    attributes = lb.get_attributes()

    attributes.cross_zone_load_balancing.enabled.should.be.false
    attributes.connection_draining.enabled.should.be.false
    attributes.access_log.enabled.should.be.false
    attributes.connecting_settings.idle_timeout.should.equal(60)


@mock_elb
def test_cross_zone_load_balancing_attribute():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    conn.modify_lb_attribute("my-lb", "CrossZoneLoadBalancing", True)
    attributes = lb.get_attributes(force=True)
    attributes.cross_zone_load_balancing.enabled.should.be.true

    conn.modify_lb_attribute("my-lb", "CrossZoneLoadBalancing", False)
    attributes = lb.get_attributes(force=True)
    attributes.cross_zone_load_balancing.enabled.should.be.false


@mock_elb
def test_connection_draining_attribute():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    connection_draining = ConnectionDrainingAttribute()
    connection_draining.enabled = True
    connection_draining.timeout = 60

    conn.modify_lb_attribute("my-lb", "ConnectionDraining", connection_draining)
    attributes = lb.get_attributes(force=True)
    attributes.connection_draining.enabled.should.be.true
    attributes.connection_draining.timeout.should.equal(60)

    connection_draining.timeout = 30
    conn.modify_lb_attribute("my-lb", "ConnectionDraining", connection_draining)
    attributes = lb.get_attributes(force=True)
    attributes.connection_draining.timeout.should.equal(30)

    connection_draining.enabled = False
    conn.modify_lb_attribute("my-lb", "ConnectionDraining", connection_draining)
    attributes = lb.get_attributes(force=True)
    attributes.connection_draining.enabled.should.be.false


@mock_elb
def test_access_log_attribute():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    access_log = AccessLogAttribute()
    access_log.enabled = True
    access_log.s3_bucket_name = 'bucket'
    access_log.s3_bucket_prefix = 'prefix'
    access_log.emit_interval = 60

    conn.modify_lb_attribute("my-lb", "AccessLog", access_log)
    attributes = lb.get_attributes(force=True)
    attributes.access_log.enabled.should.be.true
    attributes.access_log.s3_bucket_name.should.equal("bucket")
    attributes.access_log.s3_bucket_prefix.should.equal("prefix")
    attributes.access_log.emit_interval.should.equal(60)

    access_log.enabled = False
    conn.modify_lb_attribute("my-lb", "AccessLog", access_log)
    attributes = lb.get_attributes(force=True)
    attributes.access_log.enabled.should.be.false


@mock_elb
def test_connection_settings_attribute():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)

    connection_settings = ConnectionSettingAttribute(conn)
    connection_settings.idle_timeout = 120

    conn.modify_lb_attribute("my-lb", "ConnectingSettings", connection_settings)
    attributes = lb.get_attributes(force=True)
    attributes.connecting_settings.idle_timeout.should.equal(120)

    connection_settings.idle_timeout = 60
    conn.modify_lb_attribute("my-lb", "ConnectingSettings", connection_settings)
    attributes = lb.get_attributes(force=True)
    attributes.connecting_settings.idle_timeout.should.equal(60)

@mock_elb
def test_create_lb_cookie_stickiness_policy():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    cookie_expiration_period = 60
    policy_name = "LBCookieStickinessPolicy"

    lb.create_cookie_stickiness_policy(cookie_expiration_period, policy_name)

    lb = conn.get_all_load_balancers()[0]
    # There appears to be a quirk about boto, whereby it returns a unicode
    # string for cookie_expiration_period, despite being stated in
    # documentation to be a long numeric.
    #
    # To work around that, this value is converted to an int and checked.
    cookie_expiration_period_response_str = lb.policies.lb_cookie_stickiness_policies[0].cookie_expiration_period
    int(cookie_expiration_period_response_str).should.equal(cookie_expiration_period)
    lb.policies.lb_cookie_stickiness_policies[0].policy_name.should.equal(policy_name)

@mock_elb
def test_create_lb_cookie_stickiness_policy_no_expiry():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    policy_name = "LBCookieStickinessPolicy"

    lb.create_cookie_stickiness_policy(None, policy_name)

    lb = conn.get_all_load_balancers()[0]
    lb.policies.lb_cookie_stickiness_policies[0].cookie_expiration_period.should.be.none
    lb.policies.lb_cookie_stickiness_policies[0].policy_name.should.equal(policy_name)

@mock_elb
def test_create_app_cookie_stickiness_policy():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    cookie_name = "my-stickiness-policy"
    policy_name = "AppCookieStickinessPolicy"

    lb.create_app_cookie_stickiness_policy(cookie_name, policy_name)

    lb = conn.get_all_load_balancers()[0]
    lb.policies.app_cookie_stickiness_policies[0].cookie_name.should.equal(cookie_name)
    lb.policies.app_cookie_stickiness_policies[0].policy_name.should.equal(policy_name)

@mock_elb
def test_create_lb_policy():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    policy_name = "ProxyPolicy"

    lb.create_lb_policy(policy_name, 'ProxyProtocolPolicyType', {'ProxyProtocol': True})

    lb = conn.get_all_load_balancers()[0]
    lb.policies.other_policies[0].policy_name.should.equal(policy_name)

@mock_elb
def test_set_policies_of_listener():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    listener_port = 80
    policy_name = "my-stickiness-policy"

    # boto docs currently state that zero or one policy may be associated
    # with a given listener

    # in a real flow, it is necessary first to create a policy,
    # then to set that policy to the listener
    lb.create_cookie_stickiness_policy(None, policy_name)
    lb.set_policies_of_listener(listener_port, [policy_name])

    lb = conn.get_all_load_balancers()[0]
    listener = lb.listeners[0]
    listener.load_balancer_port.should.equal(listener_port)
    # by contrast to a backend, a listener stores only policy name strings
    listener.policy_names[0].should.equal(policy_name)

@mock_elb
def test_set_policies_of_backend_server():
    conn = boto.connect_elb()
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', [], ports)
    instance_port = 8080
    policy_name = "ProxyPolicy"

    # in a real flow, it is necessary first to create a policy,
    # then to set that policy to the backend
    lb.create_lb_policy(policy_name, 'ProxyProtocolPolicyType', {'ProxyProtocol': True}) 
    lb.set_policies_of_backend_server(instance_port, [policy_name])

    lb = conn.get_all_load_balancers()[0]
    backend = lb.backends[0]
    backend.instance_port.should.equal(instance_port)
    # by contrast to a listener, a backend stores OtherPolicy objects
    backend.policies[0].policy_name.should.equal(policy_name)

@mock_ec2
@mock_elb
def test_describe_instance_health():
    ec2_conn = boto.connect_ec2()
    reservation = ec2_conn.run_instances('ami-1234abcd', 2)
    instance_id1 = reservation.instances[0].id
    instance_id2 = reservation.instances[1].id

    conn = boto.connect_elb()
    zones = ['us-east-1a', 'us-east-1b']
    ports = [(80, 8080, 'http'), (443, 8443, 'tcp')]
    lb = conn.create_load_balancer('my-lb', zones, ports)

    instances_health = conn.describe_instance_health('my-lb')
    instances_health.should.be.empty

    lb.register_instances([instance_id1, instance_id2])

    instances_health = conn.describe_instance_health('my-lb')
    instances_health.should.have.length_of(2)
    for instance_health in instances_health:
        instance_health.instance_id.should.be.within([instance_id1, instance_id2])
        instance_health.state.should.equal('InService')

    instances_health = conn.describe_instance_health('my-lb', [instance_id1])
    instances_health.should.have.length_of(1)
    instances_health[0].instance_id.should.equal(instance_id1)
    instances_health[0].state.should.equal('InService')
