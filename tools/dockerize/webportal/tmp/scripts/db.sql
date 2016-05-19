/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
DROP DATABASE IF EXISTS `test`;
DELETE FROM mysql.user WHERE user='';
GRANT ALL PRIVILEGES ON daoliweb.* TO 'daoliweb'@'localhost' IDENTIFIED BY 'daoli123';
GRANT ALL PRIVILEGES ON daoliweb.* TO 'daoliweb'@'%' IDENTIFIED BY 'daoli123';
GRANT ALL PRIVILEGES ON *.* TO 'daolisst'@'%' IDENTIFIED BY 'daoli123';
FLUSH PRIVILEGES;
CREATE DATABASE IF NOT EXISTS `daoliweb`;
USE `daoliweb`;

--
-- Table structure for table `daoli_bill_total`
--

DROP TABLE IF EXISTS `daoli_bill_total`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_bill_total` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `project_id` varchar(36) NOT NULL,
  `balance` varchar(20) DEFAULT '0.0000',
  `total_cost` varchar(20) DEFAULT '0.0000',
  `email_time` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_container_bill_info`
--

DROP TABLE IF EXISTS `daoli_container_bill_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_container_bill_info` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `project_id` varchar(36) NOT NULL,
  `container_id` varchar(36) NOT NULL,
  `status` varchar(10) DEFAULT NULL,
  `container_name` varchar(50) DEFAULT NULL,
  `container_zone` varchar(50) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `flavor_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1093 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_container_cost_details`
--

DROP TABLE IF EXISTS `daoli_container_cost_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_container_cost_details` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `project_id` varchar(36) NOT NULL,
  `container_id` varchar(36) NOT NULL,
  `container_name` varchar(255) DEFAULT NULL,
  `container_cost` varchar(20) DEFAULT '0.0000',
  `container_zone` varchar(50) DEFAULT NULL,
  `runtime` varchar(10) DEFAULT '0',
  `status` varchar(10) DEFAULT NULL,
  `flavor_id` varchar(36) DEFAULT NULL,
  `update_time` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_container_flavor_price`
--

DROP TABLE IF EXISTS `daoli_container_flavor_price`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_container_flavor_price` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `flavor_id` varchar(36) NOT NULL,
  `flavor_name` varchar(20) DEFAULT NULL,
  `flavor_cpu` int(11) DEFAULT '0',
  `flavor_memory` int(11) DEFAULT '0',
  `flavor_disk` int(11) DEFAULT '0',
  `flavor_network` int(11) DEFAULT '0',
  `flavor_zone` varchar(50) DEFAULT NULL,
  `flavor_price` varchar(10) DEFAULT '0.0000',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_disk_bill_info`
--

DROP TABLE IF EXISTS `daoli_disk_bill_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_disk_bill_info` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `project_id` varchar(36) NOT NULL,
  `disk_id` varchar(36) DEFAULT NULL,
  `status` varchar(10) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `deleted_at` datetime DEFAULT NULL,
  `disk_name` varchar(255) DEFAULT NULL,
  `disk_size` int(11) DEFAULT NULL,
  `disk_zone` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=230 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_disk_cost_details`
--

DROP TABLE IF EXISTS `daoli_disk_cost_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_disk_cost_details` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `project_id` varchar(36) NOT NULL,
  `disk_id` varchar(64) DEFAULT NULL,
  `disk_name` varchar(255) DEFAULT NULL,
  `disk_size` int(11) DEFAULT '0',
  `disk_cost` varchar(20) DEFAULT NULL,
  `disk_zone` varchar(50) DEFAULT NULL,
  `runtime` varchar(10) DEFAULT NULL,
  `status` varchar(10) DEFAULT NULL,
  `update_time` date DEFAULT NULL,
  `instance_id` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `daoli_disk_zone_price`
--

DROP TABLE IF EXISTS `daoli_disk_zone_price`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `daoli_disk_zone_price` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `zone_name` varchar(50) DEFAULT NULL,
  `price` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `firewalls`
--

DROP TABLE IF EXISTS `firewalls`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `firewalls` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `hostname` varchar(255) NOT NULL,
  `gateway_port` int(11) NOT NULL,
  `service_port` int(11) NOT NULL,
  `instance_id` varchar(36) NOT NULL,
  `fake_zone` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=148 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `flavors`
--

DROP TABLE IF EXISTS `flavors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
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
  `zone` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `gateways`
--

DROP TABLE IF EXISTS `gateways`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `gateways` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `datapath_id` varchar(100) NOT NULL,
  `hostname` varchar(100) NOT NULL,
  `idc_id` int(11) NOT NULL,
  `idc_mac` varchar(64) DEFAULT NULL,
  `vint_dev` varchar(100) NOT NULL,
  `vint_mac` varchar(64) NOT NULL,
  `vext_dev` varchar(100) NOT NULL,
  `vext_ip` varchar(64),
  `ext_dev` varchar(100) NOT NULL,
  `ext_mac` varchar(64) NOT NULL,
  `ext_ip` varchar(64) NOT NULL,
  `int_dev` varchar(100) NOT NULL,
  `int_mac` varchar(64) NOT NULL,
  `int_ip` varchar(64) DEFAULT NULL,
  `zone` varchar(36) NOT NULL,
  `count` int(11) NOT NULL,
  `is_gateway` tinyint(1) DEFAULT 0,
  `disabled` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `images`
--

DROP TABLE IF EXISTS `images`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `images` (
  `id` varchar(36) NOT NULL,
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
  `zone` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `instances`
--

DROP TABLE IF EXISTS `instances`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `instances` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `address` varchar(15) DEFAULT NULL,
  `mac_address` varchar(17) DEFAULT NULL,
  `phy_ipv4` varchar(15) DEFAULT NULL,
  `host` varchar(100) DEFAULT NULL,
  `project_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  `availability_zone` varchar(36) NOT NULL,
  `image` varchar(36) NOT NULL,
  `flavor` varchar(36) NOT NULL,
  `status` varchar(10) DEFAULT NULL,
  `power_state` int(11) DEFAULT NULL,
  `fake_hostname` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ipallocationpools`
--

DROP TABLE IF EXISTS `ipallocationpools`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ipallocationpools` (
  `id` varchar(36) NOT NULL,
  `subnet_id` varchar(36) DEFAULT NULL,
  `first_ip` varchar(64) NOT NULL,
  `last_ip` varchar(64) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `subnet_id` (`subnet_id`),
  CONSTRAINT `ipallocationpools_ibfk_1` FOREIGN KEY (`subnet_id`) REFERENCES `subnets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ipavailabilityranges`
--

DROP TABLE IF EXISTS `ipavailabilityranges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ipavailabilityranges` (
  `allocation_pool_id` varchar(36) NOT NULL,
  `first_ip` varchar(64) NOT NULL,
  `last_ip` varchar(64) NOT NULL,
  PRIMARY KEY (`allocation_pool_id`),
  CONSTRAINT `ipavailabilityranges_ibfk_1` FOREIGN KEY (`allocation_pool_id`) REFERENCES `ipallocationpools` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `network_types`
--

DROP TABLE IF EXISTS `network_types`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `network_types` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `cidr` varchar(64) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `networks`
--

DROP TABLE IF EXISTS `networks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `networks` (
  `id` varchar(36) NOT NULL,
  `gateway` varchar(64) DEFAULT NULL,
  `netype` int(11) NOT NULL,
  `zone_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_networks`
--

DROP TABLE IF EXISTS `project_networks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `project_networks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `third` int(11) NOT NULL,
  `fourth` int(11) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `resources`
--

DROP TABLE IF EXISTS `resources`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `resources` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `source_name` varchar(255) NOT NULL,
  `source_id` varchar(255) NOT NULL,
  `action` varchar(255) NOT NULL,
  `extra` mediumtext,
  `project_id` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=352 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `services` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `url` varchar(255) NOT NULL,
  `topic` varchar(20) DEFAULT NULL,
  `idc_id` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `single_security_groups`
--

DROP TABLE IF EXISTS `single_security_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `single_security_groups` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `top` varchar(36) NOT NULL,
  `bottom` varchar(36) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_single_security_group0top0bottom0user_id` (`top`,`bottom`,`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=67 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `subnets`
--

DROP TABLE IF EXISTS `subnets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `subnets` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `cidr` varchar(64) NOT NULL,
  `gateway_ip` varchar(64) DEFAULT NULL,
  `net_type` int(11) NOT NULL,
  `user_id` varchar(36) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `token`
--

DROP TABLE IF EXISTS `token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `token` (
  `id` varchar(64) NOT NULL,
  `expires` datetime DEFAULT NULL,
  `extra` text,
  `user_id` varchar(64) DEFAULT NULL,
  `project_id` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_token_expires` (`expires`),
  KEY `ix_token_project_id` (`project_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `uuid` varchar(36) NOT NULL,
  `username` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `type` int(11) DEFAULT NULL,
  `phone` varchar(11) NOT NULL,
  `company` varchar(255) NOT NULL,
  `reason` varchar(255) NOT NULL,
  `enabled` tinyint(1) DEFAULT NULL,
  `extra` mediumtext,
  PRIMARY KEY (`uuid`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
INSERT INTO `user` VALUES (NOW(),NOW(),'7ece068f-b02f-4251-833a-11222ae6f201','admin','daoli123','nvi@daolicloud.com',0,'01082823993','Daolicloud.com','Administrator',true,'{}');
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_login`
--

DROP TABLE IF EXISTS `user_login`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_login` (
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) NOT NULL,
  `user_addr` varchar(17) DEFAULT NULL,
  `user_type` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_project`
--

DROP TABLE IF EXISTS `user_project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_project` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(36) NOT NULL,
  `project_id` varchar(36) NOT NULL,
  `keystone_user_id` varchar(36) NOT NULL,
  `zone_id` varchar(36) NOT NULL,
  `total_instances` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=51 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_tasks`
--

DROP TABLE IF EXISTS `user_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `utype` varchar(10) NOT NULL,
  `uobj` mediumtext,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `zones`
--

DROP TABLE IF EXISTS `zones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `zones` (
  `id` varchar(36) NOT NULL,
  `name` varchar(255) NOT NULL,
  `auth_url` varchar(255) NOT NULL,
  `token` varchar(255) NOT NULL,
  `idc_id` int(11) DEFAULT '0',
  `default_instances` int(11) NOT NULL,
  `disabled` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2015-07-01 14:46:52
