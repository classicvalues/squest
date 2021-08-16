from copy import copy

from django.urls import reverse

from resource_tracker.models import ResourceGroupAttributeDefinition
from resource_tracker.tests.base_test_resource_tracker import BaseTestResourceTracker


class TestResourceGroupAttributeViews(BaseTestResourceTracker):

    def setUp(self):
        super(TestResourceGroupAttributeViews, self).setUp()

    def test_resource_group_attribute_create(self):
        args = {
            "resource_group_id": self.rg_physical_servers.id,
        }
        url = reverse('resource_tracker:resource_group_attribute_create', kwargs=args)

        # test GET
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)
        self.assertTrue("resource_group" in response.context)

        # test POST without producer or consumer
        new_name = "new_attribute_name"
        data = {
            "name": new_name
        }
        number_attribute_before = ResourceGroupAttributeDefinition.objects.all().count()
        response = self.client.post(url, data=data)
        self.assertEquals(302, response.status_code)
        self.assertEquals(number_attribute_before + 1, ResourceGroupAttributeDefinition.objects.all().count())
        self.assertTrue(ResourceGroupAttributeDefinition.objects.filter(name="new_attribute_name",
                                                                        resource_group_definition=self.rg_physical_servers).exists())

        # test POST with producer
        new_name = "new_attribute_name_2"
        data = {
            "name": new_name,
            "produce_for": self.rp_vcenter_vcpu_attribute.id
        }
        response = self.client.post(url, data=data)
        self.assertEquals(302, response.status_code)
        self.assertTrue(ResourceGroupAttributeDefinition.objects.filter(name="new_attribute_name_2",
                                                                        resource_group_definition=self.rg_physical_servers).exists())
        target_rga = ResourceGroupAttributeDefinition.objects.get(name="new_attribute_name_2",
                                                                  resource_group_definition=self.rg_physical_servers)
        self.assertEquals(target_rga.produce_for, self.rp_vcenter_vcpu_attribute)

    def test_resource_group_attribute_edit(self):
        args = {
            "resource_group_id": self.rg_physical_servers.id,
            "attribute_id": self.rg_physical_servers_cpu_attribute.id
        }
        url = reverse('resource_tracker:resource_group_attribute_edit', kwargs=args)

        # test GET
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)

        # test POST without producer or consumer
        new_name = "new_attribute_name"
        data = {
            "name": new_name
        }
        response = self.client.post(url, data=data)
        self.assertEquals(302, response.status_code)
        self.rg_physical_servers_cpu_attribute.refresh_from_db()
        self.assertEquals(self.rg_physical_servers_cpu_attribute.name, "new_attribute_name")

    def test_resource_group_attribute_delete(self):
        args = {
            "resource_group_id": self.rg_physical_servers.id,
            "attribute_id": self.rg_physical_servers_cpu_attribute.id
        }
        url = reverse('resource_tracker:resource_group_attribute_delete', kwargs=args)

        # test GET
        response = self.client.get(url)
        self.assertEquals(200, response.status_code)

        # test POST
        attribute_id = copy(self.rg_physical_servers_cpu_attribute.id)
        self.assertTrue(ResourceGroupAttributeDefinition.objects.filter(id=attribute_id).exists())
        response = self.client.post(url)
        self.assertEquals(302, response.status_code)
        self.assertFalse(ResourceGroupAttributeDefinition.objects.filter(id=attribute_id).exists())