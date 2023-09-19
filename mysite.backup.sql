-- MySQL dump 10.13  Distrib 8.0.34, for Linux (x86_64)
--
-- Host: localhost    Database: mysite
-- ------------------------------------------------------
-- Server version	8.0.34-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `account_account`
--

DROP TABLE IF EXISTS `account_account`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_account` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `register_time` date NOT NULL,
  `photo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` smallint NOT NULL,
  `shipping_address` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `account_account_user_id_8d4f4816_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_account`
--

LOCK TABLES `account_account` WRITE;
/*!40000 ALTER TABLE `account_account` DISABLE KEYS */;
/*!40000 ALTER TABLE `account_account` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `account_userprofile`
--

DROP TABLE IF EXISTS `account_userprofile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `account_userprofile` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `first_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `company` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `department` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `phone` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `register_time` date NOT NULL,
  `photo` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `level` smallint NOT NULL,
  `shipping_address` varchar(500) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `account_userprofile_user_id_5afa3c7a_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `account_userprofile`
--

LOCK TABLES `account_userprofile` WRITE;
/*!40000 ALTER TABLE `account_userprofile` DISABLE KEYS */;
INSERT INTO `account_userprofile` VALUES (1,'','','','','',NULL,'2023-09-06','',1,'',1);
/*!40000 ALTER TABLE `account_userprofile` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group`
--

LOCK TABLES `auth_group` WRITE;
/*!40000 ALTER TABLE `auth_group` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `group_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_group_permissions`
--

LOCK TABLES `auth_group_permissions` WRITE;
/*!40000 ALTER TABLE `auth_group_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_group_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int NOT NULL,
  `codename` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=81 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add shopping cart',7,'add_shoppingcart'),(26,'Can change shopping cart',7,'change_shoppingcart'),(27,'Can delete shopping cart',7,'delete_shoppingcart'),(28,'Can view shopping cart',7,'view_shoppingcart'),(29,'Can add account',8,'add_account'),(30,'Can change account',8,'change_account'),(31,'Can delete account',8,'delete_account'),(32,'Can view account',8,'view_account'),(33,'Can add product',9,'add_product'),(34,'Can change product',9,'change_product'),(35,'Can delete product',9,'delete_product'),(36,'Can view product',9,'view_product'),(37,'Can add order',10,'add_order'),(38,'Can change order',10,'change_order'),(39,'Can delete order',10,'delete_order'),(40,'Can view order',10,'view_order'),(41,'Can add shopping cart detail',11,'add_shoppingcartdetail'),(42,'Can change shopping cart detail',11,'change_shoppingcartdetail'),(43,'Can delete shopping cart detail',11,'delete_shoppingcartdetail'),(44,'Can view shopping cart detail',11,'view_shoppingcartdetail'),(45,'Can add order detail',12,'add_orderdetail'),(46,'Can change order detail',12,'change_orderdetail'),(47,'Can delete order detail',12,'delete_orderdetail'),(48,'Can view order detail',12,'view_orderdetail'),(49,'Can add shopping cart',13,'add_shoppingcart'),(50,'Can change shopping cart',13,'change_shoppingcart'),(51,'Can delete shopping cart',13,'delete_shoppingcart'),(52,'Can view shopping cart',13,'view_shoppingcart'),(53,'Can add expression_host',14,'add_expression_host'),(54,'Can change expression_host',14,'change_expression_host'),(55,'Can delete expression_host',14,'delete_expression_host'),(56,'Can view expression_host',14,'view_expression_host'),(57,'Can add addon',15,'add_addon'),(58,'Can change addon',15,'change_addon'),(59,'Can delete addon',15,'delete_addon'),(60,'Can view addon',15,'view_addon'),(61,'Can add expression scale',16,'add_expressionscale'),(62,'Can change expression scale',16,'change_expressionscale'),(63,'Can delete expression scale',16,'delete_expressionscale'),(64,'Can view expression scale',16,'view_expressionscale'),(65,'Can add purification_method',17,'add_purification_method'),(66,'Can change purification_method',17,'change_purification_method'),(67,'Can delete purification_method',17,'delete_purification_method'),(68,'Can view purification_method',17,'view_purification_method'),(69,'Can add expression host',14,'add_expressionhost'),(70,'Can change expression host',14,'change_expressionhost'),(71,'Can delete expression host',14,'delete_expressionhost'),(72,'Can view expression host',14,'view_expressionhost'),(73,'Can add purification method',17,'add_purificationmethod'),(74,'Can change purification method',17,'change_purificationmethod'),(75,'Can delete purification method',17,'delete_purificationmethod'),(76,'Can view purification method',17,'view_purificationmethod'),(77,'Can add user profile',18,'add_userprofile'),(78,'Can change user profile',18,'change_userprofile'),(79,'Can delete user profile',18,'delete_userprofile'),(80,'Can view user profile',18,'view_userprofile');
/*!40000 ALTER TABLE `auth_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int NOT NULL AUTO_INCREMENT,
  `password` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `first_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `last_name` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$390000$hbeAsSW51oyUMO9WbKlJAD$JpsBRSbyJv1WcuW4Atfu39viNfx7pyOuQgOh1lgTynE=','2023-09-12 11:32:38.977442',1,'dushiyi','','','',1,1,'2023-08-23 12:08:19.150374'),(2,'pbkdf2_sha256$390000$wwJ0FWBaKCXjRbQ0xDdP94$u3RfjJBosk40pywfmqK3a0gKkcpDjF5wbfMQbbcCaUk=','2023-08-27 03:59:07.012458',1,'admin','','','',1,1,'2023-08-27 02:50:35.296977'),(3,'',NULL,0,'temp_user','','','',0,1,'2023-09-06 00:28:49.654421');
/*!40000 ALTER TABLE `auth_user` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `group_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_groups`
--

LOCK TABLES `auth_user_groups` WRITE;
/*!40000 ALTER TABLE `auth_user_groups` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_groups` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `permission_id` int NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user_user_permissions`
--

LOCK TABLES `auth_user_user_permissions` WRITE;
/*!40000 ALTER TABLE `auth_user_user_permissions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_user_user_permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext COLLATE utf8mb4_unicode_ci,
  `object_repr` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `action_flag` smallint unsigned NOT NULL,
  `change_message` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `content_type_id` int DEFAULT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `django_admin_log_chk_1` CHECK ((`action_flag` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=55 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2023-08-27 04:10:29.752715','1','Fast Plasmid',1,'[{\"added\": {}}]',9,2),(2,'2023-08-27 04:11:29.014143','2','HT Plasmid',1,'[{\"added\": {}}]',9,2),(3,'2023-08-27 04:12:28.932858','3','Fast Antibody',1,'[{\"added\": {}}]',9,2),(4,'2023-08-27 04:13:16.259624','4','HT Antibody',1,'[{\"added\": {}}]',9,2),(5,'2023-08-27 04:16:22.088959','5','SEC-HPLC',1,'[{\"added\": {}}]',9,2),(6,'2023-08-27 04:16:55.821465','6','Endotoxin',1,'[{\"added\": {}}]',9,2),(7,'2023-08-30 06:15:09.606376','6','Endotoxin',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(8,'2023-08-30 06:15:15.290343','5','SEC-HPLC',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(9,'2023-08-30 06:15:20.508254','4','HT Antibody',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(10,'2023-08-30 06:15:27.343043','4','HT Antibody',2,'[]',9,1),(11,'2023-08-30 06:15:33.460664','3','Fast Antibody',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(12,'2023-08-30 06:15:38.793929','2','HT Plasmid',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(13,'2023-08-30 06:15:44.640581','1','Fast Plasmid',2,'[{\"changed\": {\"fields\": [\"Price\"]}}]',9,1),(14,'2023-08-30 15:28:22.609072','1','Order object (1)',3,'',10,1),(15,'2023-08-30 15:28:29.685665','2','Order object (2)',3,'',10,1),(16,'2023-08-30 15:28:35.867342','3','Order object (3)',3,'',10,1),(17,'2023-08-30 15:28:41.527387','4','Order object (4)',3,'',10,1),(18,'2023-08-30 15:37:21.119337','8','Order object (8)',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',10,1),(19,'2023-09-04 10:49:54.340592','1','30ml',1,'[{\"added\": {}}]',16,1),(20,'2023-09-04 10:50:10.880593','2','3ml',1,'[{\"added\": {}}]',16,1),(21,'2023-09-04 10:50:41.235052','1','293F',1,'[{\"added\": {}}]',14,1),(22,'2023-09-04 10:50:56.584309','2','CHO',1,'[{\"added\": {}}]',14,1),(23,'2023-09-04 10:53:50.405460','1','Protein A',1,'[{\"added\": {}}]',17,1),(24,'2023-09-04 10:54:06.720280','2','Protein G',1,'[{\"added\": {}}]',17,1),(25,'2023-09-04 10:58:22.745724','1','SEC-HPLC',1,'[{\"added\": {}}]',15,1),(26,'2023-09-04 10:58:59.768407','2','Endotoxin',1,'[{\"added\": {}}]',15,1),(27,'2023-09-06 04:11:27.219706','38','ShoppingCart object (38)',3,'',13,1),(28,'2023-09-06 04:11:34.634692','37','ShoppingCart object (37)',3,'',13,1),(29,'2023-09-06 04:11:41.568685','36','ShoppingCart object (36)',3,'',13,1),(30,'2023-09-06 04:11:48.916611','35','ShoppingCart object (35)',3,'',13,1),(31,'2023-09-06 04:11:58.728943','34','ShoppingCart object (34)',3,'',13,1),(32,'2023-09-06 04:12:10.759252','33','ShoppingCart object (33)',3,'',13,1),(33,'2023-09-06 04:12:17.761569','32','ShoppingCart object (32)',3,'',13,1),(34,'2023-09-06 08:45:18.840559','12','ShoppingCart object (12)',3,'',13,1),(35,'2023-09-06 08:45:27.231314','15','ShoppingCart object (15)',3,'',13,1),(36,'2023-09-06 08:45:35.429481','16','ShoppingCart object (16)',3,'',13,1),(37,'2023-09-06 08:45:44.966397','17','ShoppingCart object (17)',3,'',13,1),(38,'2023-09-06 08:45:56.115352','18','ShoppingCart object (18)',3,'',13,1),(39,'2023-09-06 08:46:05.135303','19','ShoppingCart object (19)',3,'',13,1),(40,'2023-09-06 08:46:14.886396','20','ShoppingCart object (20)',3,'',13,1),(41,'2023-09-06 08:46:24.380864','22','ShoppingCart object (22)',3,'',13,1),(42,'2023-09-06 08:46:33.224780','24','ShoppingCart object (24)',3,'',13,1),(43,'2023-09-06 08:46:42.337752','25','ShoppingCart object (25)',3,'',13,1),(44,'2023-09-06 08:46:54.948024','26','ShoppingCart object (26)',3,'',13,1),(45,'2023-09-06 08:47:09.852194','27','ShoppingCart object (27)',3,'',13,1),(46,'2023-09-06 08:55:52.668310','28','ShoppingCart object (28)',3,'',13,1),(47,'2023-09-06 08:55:59.769636','29','ShoppingCart object (29)',3,'',13,1),(48,'2023-09-06 08:56:08.316086','30','ShoppingCart object (30)',3,'',13,1),(49,'2023-09-09 13:09:49.035305','31','31',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1),(50,'2023-09-09 13:21:53.012904','40','40',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1),(51,'2023-09-09 13:22:01.278141','41','41',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1),(52,'2023-09-09 13:22:10.196684','42','42',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1),(53,'2023-09-09 14:35:36.169114','31','31',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1),(54,'2023-09-09 14:36:51.758473','42','42',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',13,1);
/*!40000 ALTER TABLE `django_admin_log` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `model` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (8,'account','account'),(7,'account','shoppingcart'),(18,'account','userprofile'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(15,'product','addon'),(14,'product','expressionhost'),(16,'product','expressionscale'),(9,'product','product'),(17,'product','purificationmethod'),(6,'sessions','session'),(10,'user_center','order'),(12,'user_center','orderdetail'),(13,'user_center','shoppingcart'),(11,'user_center','shoppingcartdetail');
/*!40000 ALTER TABLE `django_content_type` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `app` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'product','0001_initial','2023-08-23 12:07:47.757238'),(2,'contenttypes','0001_initial','2023-08-23 12:07:47.847242'),(3,'auth','0001_initial','2023-08-23 12:07:48.532562'),(4,'account','0001_initial','2023-08-23 12:07:48.804093'),(5,'admin','0001_initial','2023-08-23 12:07:48.984652'),(6,'admin','0002_logentry_remove_auto_add','2023-08-23 12:07:49.001298'),(7,'admin','0003_logentry_add_action_flag_choices','2023-08-23 12:07:49.018303'),(8,'contenttypes','0002_remove_content_type_name','2023-08-23 12:07:49.117888'),(9,'auth','0002_alter_permission_name_max_length','2023-08-23 12:07:49.187178'),(10,'auth','0003_alter_user_email_max_length','2023-08-23 12:07:49.234396'),(11,'auth','0004_alter_user_username_opts','2023-08-23 12:07:49.248068'),(12,'auth','0005_alter_user_last_login_null','2023-08-23 12:07:49.318648'),(13,'auth','0006_require_contenttypes_0002','2023-08-23 12:07:49.323759'),(14,'auth','0007_alter_validators_add_error_messages','2023-08-23 12:07:49.337027'),(15,'auth','0008_alter_user_username_max_length','2023-08-23 12:07:49.404762'),(16,'auth','0009_alter_user_last_name_max_length','2023-08-23 12:07:49.513979'),(17,'auth','0010_alter_group_name_max_length','2023-08-23 12:07:49.548956'),(18,'auth','0011_update_proxy_permissions','2023-08-23 12:07:49.562438'),(19,'auth','0012_alter_user_first_name_max_length','2023-08-23 12:07:49.622418'),(20,'sessions','0001_initial','2023-08-23 12:07:49.675890'),(21,'user_center','0001_initial','2023-08-23 12:07:50.033954'),(22,'product','0002_product_express_host_product_number_of_antibody_and_more','2023-08-27 02:44:36.080174'),(23,'product','0003_remove_product_number_of_antibody','2023-08-27 04:20:15.043776'),(24,'user_center','0002_shoppingcart_alter_shoppingcartdetail_cart','2023-08-29 11:54:07.117425'),(25,'account','0002_delete_shoppingcart','2023-08-29 11:54:07.150040'),(26,'product','0004_remove_product_express_host_and_more','2023-08-30 06:00:14.530427'),(27,'user_center','0002_alter_shoppingcart_user','2023-08-30 09:42:45.066029'),(28,'product','0002_rename_turnaroud_time_product_turnaround_time','2023-08-30 13:24:24.059547'),(29,'user_center','0003_order_shopping_cart','2023-08-30 15:19:40.258709'),(30,'user_center','0004_remove_shoppingcartdetail_cart_and_more','2023-08-30 15:19:40.530987'),(31,'product','0003_purification_method_expressionscale_expression_host_and_more','2023-09-04 10:47:14.633884'),(32,'product','0004_addon_desc_addon_turnaround_time','2023-09-04 10:56:03.169901'),(33,'product','0002_rename_expression_host_expressionhost_and_more','2023-09-06 02:40:53.796817'),(34,'user_center','0002_alter_shoppingcart_express_host_and_more','2023-09-06 09:51:19.016999'),(35,'account','0002_userprofile','2023-09-06 15:08:12.949275'),(36,'user_center','0003_alter_shoppingcart_status','2023-09-09 12:31:26.217690'),(37,'user_center','0004_alter_shoppingcart_project_name','2023-09-09 13:09:11.071629'),(38,'user_center','0005_alter_shoppingcart_status','2023-09-12 11:21:07.390889'),(39,'user_center','0006_shoppingcart_sequence_file','2023-09-12 11:21:07.461990');
/*!40000 ALTER TABLE `django_migrations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `session_data` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_session`
--

LOCK TABLES `django_session` WRITE;
/*!40000 ALTER TABLE `django_session` DISABLE KEYS */;
INSERT INTO `django_session` VALUES ('6yryj53ybi0b2xv7suwjgatiwet2nkbr','.eJxVjMsOwiAQRf-FtSHDYyi4dO83EB6DVA0kpV0Z_12bdKHbe865L-bDtla_DVr8nNmZCXb63WJID2o7yPfQbp2n3tZljnxX-EEHv_ZMz8vh_h3UMOq3NqBKkiAdZJupSAVBSYUCo0E0aKE40EVIq01GCjZR1HJyk0mgyabC3h-5sjcU:1qa7yr:xm3uaT41cCL4GfVgZHaZxkxTUxuQGSOQjtsYn_W24-k','2023-09-10 05:06:33.639691'),('d5exrlfu8jgzfs9xjtrz7p23murk9n8k','.eJxVjMsOwiAQRf-FtSHDYyi4dO83EB6DVA0kpV0Z_12bdKHbe865L-bDtla_DVr8nNmZCXb63WJID2o7yPfQbp2n3tZljnxX-EEHv_ZMz8vh_h3UMOq3NqBKkiAdZJupSAVBSYUCo0E0aKE40EVIq01GCjZR1HJyk0mgyabC3h-5sjcU:1qb04G:kkkpQlVEGQ760ZQfNKa-MOIgc151iJodwY9GH4ZDcwc','2023-09-12 14:51:44.153300'),('g4qcoqpkveqel4g0ajefr2m0eaxkh4xf','.eJxVjMsOwiAQRf-FtSHDYyi4dO83EB6DVA0kpV0Z_12bdKHbe865L-bDtla_DVr8nNmZCXb63WJID2o7yPfQbp2n3tZljnxX-EEHv_ZMz8vh_h3UMOq3NqBKkiAdZJupSAVBSYUCo0E0aKE40EVIq01GCjZR1HJyk0mgyabC3h-5sjcU:1qfYXH:C1tDnYNjcHxgAx2zQRoDt0UHI0NXrO0sKcKF8AAgD2U','2023-09-25 04:28:31.697255'),('q1b04j5djuowa0dbtcprrar31fxnnh6q','.eJxVjMsOwiAQRf-FtSHDYyi4dO83EB6DVA0kpV0Z_12bdKHbe865L-bDtla_DVr8nNmZCXb63WJID2o7yPfQbp2n3tZljnxX-EEHv_ZMz8vh_h3UMOq3NqBKkiAdZJupSAVBSYUCo0E0aKE40EVIq01GCjZR1HJyk0mgyabC3h-5sjcU:1qbKyW:pe3ycWFZv5pMU8aBrQ-MFXNrO1qWpJAPVNq5fdPCreg','2023-09-13 13:11:12.760725'),('r8naqybckiz5w9pb5pg01w7yu1cz6f0u','.eJxVjEEKwyAQAP_iuYgRdWOPvfcNsqtrTVsUYnIK_XsRcmivM8McIuC-lbB3XsOSxFVocfllhPHFdYj0xPpoMra6rQvJkcjTdnlvid-3s_0bFOxlbGHyhi0qNJCcdR44a4wEdnY5kY8WHXuvFFHEPEOknCcynpLVBA7E5wvvmDiq:1qa6vb:XuttqQacVrEdwHsG1CFxOw2pgGOTYASzDlVUIzopIw4','2023-09-10 03:59:07.030465'),('vv8tvtj1pwnt4p4p5qnupeu43kjene15','.eJxVjMsOwiAQRf-FtSHDYyi4dO83EB6DVA0kpV0Z_12bdKHbe865L-bDtla_DVr8nNmZCXb63WJID2o7yPfQbp2n3tZljnxX-EEHv_ZMz8vh_h3UMOq3NqBKkiAdZJupSAVBSYUCo0E0aKE40EVIq01GCjZR1HJyk0mgyabC3h-5sjcU:1qg1dG:y0DpGjEKgolaFPff7WuO4N9CCR40yDn6bQAIHxMqm2M','2023-09-26 11:32:38.981640');
/*!40000 ALTER TABLE `django_session` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_addon`
--

DROP TABLE IF EXISTS `product_addon`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_addon` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `desc` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `turnaround_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_addon`
--

LOCK TABLES `product_addon` WRITE;
/*!40000 ALTER TABLE `product_addon` DISABLE KEYS */;
INSERT INTO `product_addon` VALUES (1,'SEC-HPLC',120.00,'Additional Analysis','0.5 weeks'),(2,'Endotoxin',120.00,'Additional Analysis','0.5 weeks');
/*!40000 ALTER TABLE `product_addon` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_addon_product`
--

DROP TABLE IF EXISTS `product_addon_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_addon_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `addon_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_addon_product_addon_id_product_id_86d56759_uniq` (`addon_id`,`product_id`),
  KEY `product_addon_product_product_id_9740fc07_fk_product_product_id` (`product_id`),
  CONSTRAINT `product_addon_product_addon_id_1531f56a_fk_product_addon_id` FOREIGN KEY (`addon_id`) REFERENCES `product_addon` (`id`),
  CONSTRAINT `product_addon_product_product_id_9740fc07_fk_product_product_id` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_addon_product`
--

LOCK TABLES `product_addon_product` WRITE;
/*!40000 ALTER TABLE `product_addon_product` DISABLE KEYS */;
INSERT INTO `product_addon_product` VALUES (1,1,3),(2,1,4),(3,2,3),(4,2,4);
/*!40000 ALTER TABLE `product_addon_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_expressionhost`
--

DROP TABLE IF EXISTS `product_expressionhost`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_expressionhost` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `host_name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionhost`
--

LOCK TABLES `product_expressionhost` WRITE;
/*!40000 ALTER TABLE `product_expressionhost` DISABLE KEYS */;
INSERT INTO `product_expressionhost` VALUES (1,'293F'),(2,'CHO');
/*!40000 ALTER TABLE `product_expressionhost` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_expressionhost_product`
--

DROP TABLE IF EXISTS `product_expressionhost_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_expressionhost_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `expressionhost_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_expression_host__expression_host_id_produ_cc7dd1b4_uniq` (`expressionhost_id`,`product_id`),
  KEY `product_expression_h_product_id_cf388ca1_fk_product_p` (`product_id`),
  CONSTRAINT `product_expression_h_product_id_cf388ca1_fk_product_p` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`),
  CONSTRAINT `product_expressionho_expressionhost_id_6593cdb3_fk_product_e` FOREIGN KEY (`expressionhost_id`) REFERENCES `product_expressionhost` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionhost_product`
--

LOCK TABLES `product_expressionhost_product` WRITE;
/*!40000 ALTER TABLE `product_expressionhost_product` DISABLE KEYS */;
INSERT INTO `product_expressionhost_product` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,2,1),(6,2,2),(7,2,3),(8,2,4);
/*!40000 ALTER TABLE `product_expressionhost_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_expressionscale`
--

DROP TABLE IF EXISTS `product_expressionscale`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_expressionscale` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `scale` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionscale`
--

LOCK TABLES `product_expressionscale` WRITE;
/*!40000 ALTER TABLE `product_expressionscale` DISABLE KEYS */;
INSERT INTO `product_expressionscale` VALUES (1,'30ml'),(2,'3ml');
/*!40000 ALTER TABLE `product_expressionscale` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_expressionscale_product`
--

DROP TABLE IF EXISTS `product_expressionscale_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_expressionscale_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `expressionscale_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_expressionscale__expressionscale_id_produ_e95a08fa_uniq` (`expressionscale_id`,`product_id`),
  KEY `product_expressionsc_product_id_e9434521_fk_product_p` (`product_id`),
  CONSTRAINT `product_expressionsc_expressionscale_id_aac3b43a_fk_product_e` FOREIGN KEY (`expressionscale_id`) REFERENCES `product_expressionscale` (`id`),
  CONSTRAINT `product_expressionsc_product_id_e9434521_fk_product_p` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionscale_product`
--

LOCK TABLES `product_expressionscale_product` WRITE;
/*!40000 ALTER TABLE `product_expressionscale_product` DISABLE KEYS */;
INSERT INTO `product_expressionscale_product` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,2,1),(6,2,2),(7,2,3),(8,2,4);
/*!40000 ALTER TABLE `product_expressionscale_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_product`
--

DROP TABLE IF EXISTS `product_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `product_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `product_name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `turnaround_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_product`
--

LOCK TABLES `product_product` WRITE;
/*!40000 ALTER TABLE `product_product` DISABLE KEYS */;
INSERT INTO `product_product` VALUES (1,'Plasmid','59','Fast Plasmid','1 weeks'),(2,'Plasmid','19','HT Plasmid','3 weeks'),(3,'Antibody','250','Fast Antibody','2 weeks'),(4,'Antibody','90','HT Antibody','5 weeks'),(5,'Analysis','120','SEC-HPLC','0.5 weeks'),(6,'Analysis','120','Endotoxin','0.5 weeks');
/*!40000 ALTER TABLE `product_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_purificationmethod`
--

DROP TABLE IF EXISTS `product_purificationmethod`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_purificationmethod` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `method_name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_purificationmethod`
--

LOCK TABLES `product_purificationmethod` WRITE;
/*!40000 ALTER TABLE `product_purificationmethod` DISABLE KEYS */;
INSERT INTO `product_purificationmethod` VALUES (1,'Protein A'),(2,'Protein G');
/*!40000 ALTER TABLE `product_purificationmethod` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_purificationmethod_product`
--

DROP TABLE IF EXISTS `product_purificationmethod_product`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_purificationmethod_product` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `purificationmethod_id` bigint NOT NULL,
  `product_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `product_purification_met_purification_method_id_p_e180d7df_uniq` (`purificationmethod_id`,`product_id`),
  KEY `product_purification_product_id_dd393093_fk_product_p` (`product_id`),
  CONSTRAINT `product_purification_product_id_dd393093_fk_product_p` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`),
  CONSTRAINT `product_purification_purificationmethod_i_50f138d3_fk_product_p` FOREIGN KEY (`purificationmethod_id`) REFERENCES `product_purificationmethod` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_purificationmethod_product`
--

LOCK TABLES `product_purificationmethod_product` WRITE;
/*!40000 ALTER TABLE `product_purificationmethod_product` DISABLE KEYS */;
INSERT INTO `product_purificationmethod_product` VALUES (1,1,1),(2,1,2),(3,1,3),(4,1,4),(5,2,1),(6,2,2),(7,2,3),(8,2,4);
/*!40000 ALTER TABLE `product_purificationmethod_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_order`
--

DROP TABLE IF EXISTS `user_center_order`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_order` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `status` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  `shopping_cart_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_center_order_user_id_8ee12233_fk_auth_user_id` (`user_id`),
  KEY `user_center_order_shopping_cart_id_eaf99d30_fk_user_cent` (`shopping_cart_id`),
  CONSTRAINT `user_center_order_shopping_cart_id_eaf99d30_fk_user_cent` FOREIGN KEY (`shopping_cart_id`) REFERENCES `user_center_shoppingcart` (`id`),
  CONSTRAINT `user_center_order_user_id_8ee12233_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_order`
--

LOCK TABLES `user_center_order` WRITE;
/*!40000 ALTER TABLE `user_center_order` DISABLE KEYS */;
INSERT INTO `user_center_order` VALUES (12,'CREATED','2023-09-06 09:16:49.346408',1,31),(13,'CREATED','2023-09-12 11:28:33.224398',1,42);
/*!40000 ALTER TABLE `user_center_order` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_shoppingcart`
--

DROP TABLE IF EXISTS `user_center_shoppingcart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_shoppingcart` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `adding_time` datetime(6) NOT NULL,
  `status` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  `express_host_id` bigint DEFAULT NULL,
  `product_id` bigint DEFAULT NULL,
  `purification_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total_price` int DEFAULT NULL,
  `project_name` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `analysis_id` bigint DEFAULT NULL,
  `antibody_number` smallint unsigned DEFAULT NULL,
  `purification_method_id` bigint DEFAULT NULL,
  `scale_id` bigint DEFAULT NULL,
  `sequence_file` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `product_id` (`product_id`),
  KEY `user_center_shoppingcart_user_id_7ca42ad4` (`user_id`),
  KEY `user_center_shopping_analysis_id_87f66c1e_fk_product_a` (`analysis_id`),
  KEY `purification_method_id` (`purification_method_id`),
  KEY `user_center_shopping_scale_id_2efc4d72_fk_product_e` (`scale_id`),
  CONSTRAINT `user_center_shopping_analysis_id_87f66c1e_fk_product_a` FOREIGN KEY (`analysis_id`) REFERENCES `product_addon` (`id`),
  CONSTRAINT `user_center_shopping_scale_id_2efc4d72_fk_product_e` FOREIGN KEY (`scale_id`) REFERENCES `product_expressionscale` (`id`),
  CONSTRAINT `user_center_shoppingcart_ibfk_1` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`),
  CONSTRAINT `user_center_shoppingcart_ibfk_2` FOREIGN KEY (`purification_method_id`) REFERENCES `product_purificationmethod` (`id`),
  CONSTRAINT `user_center_shoppingcart_user_id_7ca42ad4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `user_center_shoppingcart_chk_1` CHECK ((`antibody_number` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_shoppingcart`
--

LOCK TABLES `user_center_shoppingcart` WRITE;
/*!40000 ALTER TABLE `user_center_shoppingcart` DISABLE KEYS */;
INSERT INTO `user_center_shoppingcart` VALUES (31,'2023-09-05 11:15:12.125582','COMPLETED',1,1,4,'',60100,NULL,2,500,1,1,NULL),(40,'2023-09-06 09:53:05.197646','INCOMPLETE',1,1,3,NULL,60100,NULL,1,500,1,1,NULL),(41,'2023-09-06 14:36:00.984601','INCOMPLETE',1,1,4,NULL,60100,NULL,1,500,1,1,NULL),(42,'2023-09-09 01:41:43.985835','INCOMPLETE',1,1,2,NULL,60100,NULL,1,500,1,1,NULL),(47,'2023-09-12 11:21:30.747181','INCOMPLETE',1,1,3,NULL,60100,NULL,1,500,1,1,NULL),(48,'2023-09-12 11:31:22.093950','INCOMPLETE',1,1,3,NULL,60100,NULL,2,500,1,1,NULL);
/*!40000 ALTER TABLE `user_center_shoppingcart` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-09-13 20:33:54
