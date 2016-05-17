#GRANT ALL PRIVILEGES ON daoliweb.* TO 'daoliweb'@'localhost' IDENTIFIED BY 'daoli123';
#GRANT ALL PRIVILEGES ON daoliweb.* TO 'daoliweb'@'%' IDENTIFIED BY 'daoli123';
#GRANT ALL PRIVILEGES ON *.* TO 'daolisst'@'%' IDENTIFIED BY 'daoli123';
#FLUSH PRIVILEGES;
#DROP DATABASE IF EXISTS `daoliweb`;
CREATE DATABASE IF NOT EXISTS `daoliweb`;
USE `daoliweb`;

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` varchar(36) NOT NULL,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `type` int(11) DEFAULT NULL,
  `phone` varchar(11),
  `company` varchar(255),
  `reason` varchar(255),
  `enabled` tinyint(1) DEFAULT NULL,
  `extra` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES (NOW(),NOW(),'7ece068f-b02f-4251-833a-11222ae6f201','admin','daoli123','nvi@daolicloud.com',0,'01082823993','Daolicloud.com','Administrator',true,'{}');
UNLOCK TABLES;



DROP TABLE IF EXISTS `user_login`;
CREATE TABLE `user_login` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) NOT NULL,
  `user_addr` varchar(17) DEFAULT NULL,
  `user_type` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



DROP TABLE IF EXISTS `user_tasks`;
CREATE TABLE `user_tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `utype` varchar(255) NOT NULL,
  `uobj` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `user_tokens`;
CREATE TABLE `user_tokens` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` varchar(36) NOT NULL ,
  `user_id` varchar(36),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;



DROP TABLE IF EXISTS `keystone_tokens`;
CREATE TABLE `keystone_tokens` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` varchar(36) NOT NULL ,
  `expires`  datetime DEFAULT NULL,
  `user_id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `user_token_id` varchar(64) NOT NULL,
  `catalog` mediumtext,
  `zone_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `services`;
CREATE TABLE `services` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `url` varchar(255) NOT NULL,
  `topic` varchar(20) DEFAULT NULL,
  `idc_id` int(11) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `zones`;
CREATE TABLE `zones` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `auth_url` varchar(255) NOT NULL,
  `auth_token` varchar(255) NOT NULL,
  `idc_id` int(11) DEFAULT 0,
  `default_instances` int(11) NOT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `instances`;
CREATE TABLE `instances` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `host` varchar(255) DEFAULT NULL,
  `keystone_project_id` varchar(36) DEFAULT NULL,
  `user_id` varchar(36) NOT NULL,
  `zone_id` varchar(36) NOT NULL,
  `image_id` varchar(36) NOT NULL,
  `flavor_id` varchar(36) NOT NULL,
  `status` varchar(10) DEFAULT NULL,
  `power_state` int(11) DEFAULT NULL,
  `fake_hostname` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `images`;
CREATE TABLE `images` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `imageid` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `checksum` varchar(32) DEFAULT NULL,
  `container_format` varchar(32) NOT NULL,
  `disk_format` varchar(32) DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `min_disk` int(11) DEFAULT NULL,
  `min_ram` int(11) DEFAULT NULL,
  `size` int(11) NOT NULL,
  `owner` varchar(32) DEFAULT NULL,
  `status` varchar(32) DEFAULT NULL,
  `property` mediumtext,
  `display_format` varchar(32) DEFAULT NULL,
  `zone_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `flavors`;
CREATE TABLE `flavors` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flavorid` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `vcpus` int(11) NOT NULL,
  `ram` int(11) NOT NULL,
  `disk` int(11) NOT NULL,
  `swap` varchar(10) DEFAULT NULL,
  `ephemeral` int(11) DEFAULT NULL,
  `rxtx_factor` float DEFAULT NULL,
  `is_public` tinyint(1) DEFAULT NULL,
  `zone_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `gateways`;
CREATE TABLE `gateways` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `datapath_id` varchar(255) NOT NULL,
  `hostname` varchar(255) NOT NULL,
  `idc_id` int(11) NOT NULL,
  `idc_mac` varchar(64) DEFAULT NULL,
  `vint_dev` varchar(255) NOT NULL,
  `vint_mac` varchar(64) NOT NULL,
  `vext_dev` varchar(255) NOT NULL,
  `vext_ip` varchar(64),
  `ext_dev` varchar(255) NOT NULL,
  `ext_mac` varchar(64) NOT NULL,
  `ext_ip` varchar(64) NOT NULL,
  `int_dev` varchar(255) NOT NULL,
  `int_mac` varchar(64) NOT NULL,
  `int_ip` varchar(64) DEFAULT NULL,
  `zone_id` varchar(36) NOT NULL,
  `count` int(11) NOT NULL,
  `is_gateway` tinyint(1) DEFAULT 0,
  `disabled` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `network_types`;
CREATE TABLE `network_types` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `cidr` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `networks`;
CREATE TABLE `networks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `networkid` varchar(36) NOT NULL,
  `gateway` varchar(64) DEFAULT NULL,
  `netype` int(11) NOT NULL,
  `zone_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `single_security_groups`;
CREATE TABLE `single_security_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `start` varchar(36) NOT NULL,
  `end` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_single_security_group0start0end0user_id` (`start`,`end`,`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;


DROP TABLE IF EXISTS `firewalls`;
CREATE TABLE `firewalls` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `gateway_port` int(11) NOT NULL,
  `service_port` int(11) NOT NULL,
  `instance_id` varchar(36) NOT NULL,
  `fake_zone` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `subnets`;
CREATE TABLE `subnets` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `cidr` varchar(64) NOT NULL,
  `gateway_ip` varchar(64) DEFAULT NULL,
  `netype` int(11) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `ipallocationpools`;
CREATE TABLE `ipallocationpools` (
  `id` varchar(36) NOT NULL,
  `subnet_id` varchar(36) DEFAULT NULL,
  `first_ip` varchar(64) NOT NULL,
  `last_ip` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `subnet_id` (`subnet_id`),
  CONSTRAINT `ipallocationpools_ibfk_1` FOREIGN KEY (`subnet_id`) REFERENCES `subnets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `ipavailabilityranges`;
CREATE TABLE `ipavailabilityranges` (
  `allocation_pool_id` varchar(36) NOT NULL,
  `first_ip` varchar(64) NOT NULL,
  `last_ip` varchar(64) NOT NULL,
  PRIMARY KEY (`allocation_pool_id`),
  CONSTRAINT `ipavailabilityranges_ibfk_1` FOREIGN KEY (`allocation_pool_id`) REFERENCES `ipallocationpools` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `instance_networks`;
CREATE TABLE `instance_networks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `address` varchar(64) DEFAULT NULL,
  `mac_address` varchar(64) DEFAULT NULL,
  `version` int(11) DEFAULT NULL,
  `network_id` varchar(36) NOT NULL,
  `instance_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

DROP TABLE IF EXISTS `resources`;
CREATE TABLE `resources` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `source_name` varchar(255) NOT NULL,
  `source_id` varchar(255) NOT NULL,
  `action` varchar(255) NOT NULL,
  `extra` mediumtext,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
