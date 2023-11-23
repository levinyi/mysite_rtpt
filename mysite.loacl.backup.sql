-- MySQL dump 10.13  Distrib 8.0.35, for Linux (x86_64)
--
-- Host: localhost    Database: mysite_rtpt
-- ------------------------------------------------------
-- Server version	8.0.35-0ubuntu0.20.04.1

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
INSERT INTO `account_userprofile` VALUES (1,'','','','','',NULL,'2023-10-25','',1,'',1);
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
) ENGINE=InnoDB AUTO_INCREMENT=89 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_permission`
--

LOCK TABLES `auth_permission` WRITE;
/*!40000 ALTER TABLE `auth_permission` DISABLE KEYS */;
INSERT INTO `auth_permission` VALUES (1,'Can add log entry',1,'add_logentry'),(2,'Can change log entry',1,'change_logentry'),(3,'Can delete log entry',1,'delete_logentry'),(4,'Can view log entry',1,'view_logentry'),(5,'Can add permission',2,'add_permission'),(6,'Can change permission',2,'change_permission'),(7,'Can delete permission',2,'delete_permission'),(8,'Can view permission',2,'view_permission'),(9,'Can add group',3,'add_group'),(10,'Can change group',3,'change_group'),(11,'Can delete group',3,'delete_group'),(12,'Can view group',3,'view_group'),(13,'Can add user',4,'add_user'),(14,'Can change user',4,'change_user'),(15,'Can delete user',4,'delete_user'),(16,'Can view user',4,'view_user'),(17,'Can add content type',5,'add_contenttype'),(18,'Can change content type',5,'change_contenttype'),(19,'Can delete content type',5,'delete_contenttype'),(20,'Can view content type',5,'view_contenttype'),(21,'Can add session',6,'add_session'),(22,'Can change session',6,'change_session'),(23,'Can delete session',6,'delete_session'),(24,'Can view session',6,'view_session'),(25,'Can add account',7,'add_account'),(26,'Can change account',7,'change_account'),(27,'Can delete account',7,'delete_account'),(28,'Can view account',7,'view_account'),(29,'Can add user profile',8,'add_userprofile'),(30,'Can change user profile',8,'change_userprofile'),(31,'Can delete user profile',8,'delete_userprofile'),(32,'Can view user profile',8,'view_userprofile'),(33,'Can add product',9,'add_product'),(34,'Can change product',9,'change_product'),(35,'Can delete product',9,'delete_product'),(36,'Can view product',9,'view_product'),(37,'Can add expression scale',10,'add_expressionscale'),(38,'Can change expression scale',10,'change_expressionscale'),(39,'Can delete expression scale',10,'delete_expressionscale'),(40,'Can view expression scale',10,'view_expressionscale'),(41,'Can add addon',11,'add_addon'),(42,'Can change addon',11,'change_addon'),(43,'Can delete addon',11,'delete_addon'),(44,'Can view addon',11,'view_addon'),(45,'Can add expression host',12,'add_expressionhost'),(46,'Can change expression host',12,'change_expressionhost'),(47,'Can delete expression host',12,'delete_expressionhost'),(48,'Can view expression host',12,'view_expressionhost'),(49,'Can add purification method',13,'add_purificationmethod'),(50,'Can change purification method',13,'change_purificationmethod'),(51,'Can delete purification method',13,'delete_purificationmethod'),(52,'Can view purification method',13,'view_purificationmethod'),(53,'Can add vector',14,'add_vector'),(54,'Can change vector',14,'change_vector'),(55,'Can delete vector',14,'delete_vector'),(56,'Can view vector',14,'view_vector'),(57,'Can add shopping cart',15,'add_shoppingcart'),(58,'Can change shopping cart',15,'change_shoppingcart'),(59,'Can delete shopping cart',15,'delete_shoppingcart'),(60,'Can view shopping cart',15,'view_shoppingcart'),(61,'Can add order',16,'add_order'),(62,'Can change order',16,'change_order'),(63,'Can delete order',16,'delete_order'),(64,'Can view order',16,'view_order'),(65,'Can add tool',17,'add_tool'),(66,'Can change tool',17,'change_tool'),(67,'Can delete tool',17,'delete_tool'),(68,'Can view tool',17,'view_tool'),(69,'Can add gene syn enzyme cut site',18,'add_genesynenzymecutsite'),(70,'Can change gene syn enzyme cut site',18,'change_genesynenzymecutsite'),(71,'Can delete gene syn enzyme cut site',18,'delete_genesynenzymecutsite'),(72,'Can view gene syn enzyme cut site',18,'view_genesynenzymecutsite'),(73,'Can add species',19,'add_species'),(74,'Can change species',19,'change_species'),(75,'Can delete species',19,'delete_species'),(76,'Can view species',19,'view_species'),(77,'Can add order info',20,'add_orderinfo'),(78,'Can change order info',20,'change_orderinfo'),(79,'Can delete order info',20,'delete_orderinfo'),(80,'Can view order info',20,'view_orderinfo'),(81,'Can add gene info',21,'add_geneinfo'),(82,'Can change gene info',21,'change_geneinfo'),(83,'Can delete gene info',21,'delete_geneinfo'),(84,'Can view gene info',21,'view_geneinfo'),(85,'Can add cart',22,'add_cart'),(86,'Can change cart',22,'change_cart'),(87,'Can delete cart',22,'delete_cart'),(88,'Can view cart',22,'view_cart');
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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_user`
--

LOCK TABLES `auth_user` WRITE;
/*!40000 ALTER TABLE `auth_user` DISABLE KEYS */;
INSERT INTO `auth_user` VALUES (1,'pbkdf2_sha256$320000$918lKGpSM0ciT62YssovH4$bvg4LHqIfINWqdmFowR3UokTj53UrQgzj+vv86x6Ug0=','2023-11-22 07:21:07.657482',1,'dushiyi','','','',1,1,'2023-10-23 06:17:30.841019'),(2,'pbkdf2_sha256$320000$gQmJX0c9urtykJRKE4RCgj$ckUPck+iHv2fwoF8t1F+SF6mrB+1rRE6+GRv13X1vrU=','2023-11-01 10:20:45.372050',0,'yanzhen','','','',0,1,'2023-11-01 10:19:26.932667'),(3,'pbkdf2_sha256$320000$nSFzUBx9Uspofr15HJIxDD$dbjSeMNjUI8U5u6ZycoKmW9ji8OgMycv9AJS7dd5K+w=','2023-11-15 10:05:15.520877',0,'test','','','',0,1,'2023-11-09 11:00:17.157623'),(4,'pbkdf2_sha256$320000$fFTxRXvn22tb6j3M3QQMHh$faKNuR24AB7ydaoXeMWlWE4TKPn6KT7OGSV5+/nF1EA=','2023-11-09 11:02:36.349112',0,'test1','','','',0,1,'2023-11-09 11:02:29.036006');
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
) ENGINE=InnoDB AUTO_INCREMENT=57 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_admin_log`
--

LOCK TABLES `django_admin_log` WRITE;
/*!40000 ALTER TABLE `django_admin_log` DISABLE KEYS */;
INSERT INTO `django_admin_log` VALUES (1,'2023-10-23 07:04:59.225496','1','Tool object (1)',1,'[{\"added\": {}}]',17,1),(2,'2023-10-25 02:55:35.145460','1','pUC19',1,'[{\"added\": {}}]',14,1),(3,'2023-10-25 02:57:58.043243','2','pCVa001M1',1,'[{\"added\": {}}]',14,1),(4,'2023-10-25 02:59:11.702776','1','pUC19',2,'[{\"changed\": {\"fields\": [\"Vector_Seq\"]}}]',14,1),(5,'2023-10-28 00:49:41.630134','1','GeneSynEnzymeCutSite object (1)',1,'[{\"added\": {}}]',18,1),(6,'2023-10-28 00:50:12.212091','2','GeneSynEnzymeCutSite object (2)',1,'[{\"added\": {}}]',18,1),(7,'2023-10-28 00:50:30.067949','3','GeneSynEnzymeCutSite object (3)',1,'[{\"added\": {}}]',18,1),(8,'2023-10-28 00:50:53.673897','4','GeneSynEnzymeCutSite object (4)',1,'[{\"added\": {}}]',18,1),(9,'2023-10-28 00:51:17.941034','5','GeneSynEnzymeCutSite object (5)',1,'[{\"added\": {}}]',18,1),(10,'2023-10-28 00:51:38.015498','6','GeneSynEnzymeCutSite object (6)',1,'[{\"added\": {}}]',18,1),(11,'2023-10-31 07:39:42.209513','1','pUC19',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(12,'2023-11-02 10:38:10.896732','1','Species object (1)',1,'[{\"added\": {}}]',19,1),(13,'2023-11-02 10:38:20.713234','2','Species object (2)',1,'[{\"added\": {}}]',19,1),(14,'2023-11-02 10:38:29.448758','3','Species object (3)',1,'[{\"added\": {}}]',19,1),(15,'2023-11-02 10:38:38.736355','4','Species object (4)',1,'[{\"added\": {}}]',19,1),(16,'2023-11-02 10:38:48.574909','5','Species object (5)',1,'[{\"added\": {}}]',19,1),(17,'2023-11-02 10:38:58.693299','6','Species object (6)',1,'[{\"added\": {}}]',19,1),(18,'2023-11-02 10:39:09.848321','7','Species object (7)',1,'[{\"added\": {}}]',19,1),(19,'2023-11-02 10:39:22.029557','8','Species object (8)',1,'[{\"added\": {}}]',19,1),(20,'2023-11-02 10:39:30.744318','9','Species object (9)',1,'[{\"added\": {}}]',19,1),(21,'2023-11-02 10:39:39.374445','10','Species object (10)',1,'[{\"added\": {}}]',19,1),(22,'2023-11-02 10:39:48.679081','11','Species object (11)',1,'[{\"added\": {}}]',19,1),(23,'2023-11-02 10:39:56.874241','12','Species object (12)',1,'[{\"added\": {}}]',19,1),(24,'2023-11-02 10:40:09.777271','13','Species object (13)',1,'[{\"added\": {}}]',19,1),(25,'2023-11-02 10:40:17.865127','14','Species object (14)',1,'[{\"added\": {}}]',19,1),(26,'2023-11-02 10:40:25.591424','15','Species object (15)',1,'[{\"added\": {}}]',19,1),(27,'2023-11-02 10:40:35.285954','16','Species object (16)',1,'[{\"added\": {}}]',19,1),(28,'2023-11-05 13:19:59.684405','18','pcDNA3.4',1,'[{\"added\": {}}]',14,1),(29,'2023-11-05 13:20:45.496518','19','pET11a',1,'[{\"added\": {}}]',14,1),(30,'2023-11-05 13:21:41.076979','20','pUC19v2',1,'[{\"added\": {}}]',14,1),(31,'2023-11-05 13:21:54.315421','20','pUC19v2',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(32,'2023-11-05 13:22:19.779009','19','pET11a',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(33,'2023-11-05 13:22:30.779808','18','pcDNA3.4',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(34,'2023-11-05 13:22:42.036620','3','SH3.6',3,'',14,1),(35,'2023-11-05 13:22:49.285601','1','pUC19',2,'[]',14,1),(36,'2023-11-05 13:23:12.009179','2','pCVa001M1',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(37,'2023-11-05 13:23:21.015779','2','pCVa001M1',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',14,1),(38,'2023-11-16 03:17:36.630941','32','NB-N-4H7',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(39,'2023-11-16 03:17:42.417579','31','NB-nsp9-4H7',2,'[]',21,1),(40,'2023-11-16 03:17:49.332906','15','pcbAB-15',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(41,'2023-11-16 03:17:54.896073','14','pcbAB-14',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(42,'2023-11-16 03:18:00.340578','13','pcbAB-13',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(43,'2023-11-16 03:18:05.458974','12','pcbAB-12',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(44,'2023-11-16 03:18:10.391548','10','pcbAB-10',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(45,'2023-11-16 03:18:16.862290','11','pcbAB-11',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(46,'2023-11-16 03:18:21.825944','10','pcbAB-10',2,'[]',21,1),(47,'2023-11-16 03:18:26.695082','9','pcbAB-13',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(48,'2023-11-16 03:18:31.806460','8','pcbAB-12',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(49,'2023-11-16 03:18:37.426427','7','pcbAB-11',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(50,'2023-11-16 03:18:42.780108','6','pcbAB-10',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(51,'2023-11-16 03:18:48.102624','5','pcbAB-9',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(52,'2023-11-16 03:18:52.391381','5','pcbAB-9',2,'[]',21,1),(53,'2023-11-16 03:18:58.927357','4','pcbAB-8',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1),(54,'2023-11-16 06:46:21.538445','35','TADAC1.19',2,'[{\"changed\": {\"fields\": [\"Status\", \"Saved seq\"]}}]',21,1),(55,'2023-11-16 06:46:45.020862','33','TADAC1.14',2,'[{\"changed\": {\"fields\": [\"Status\", \"Saved seq\"]}}]',21,1),(56,'2023-11-16 06:48:39.910507','34','TADAC1.17',2,'[{\"changed\": {\"fields\": [\"Status\"]}}]',21,1);
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
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_content_type`
--

LOCK TABLES `django_content_type` WRITE;
/*!40000 ALTER TABLE `django_content_type` DISABLE KEYS */;
INSERT INTO `django_content_type` VALUES (7,'account','account'),(8,'account','userprofile'),(1,'admin','logentry'),(3,'auth','group'),(2,'auth','permission'),(4,'auth','user'),(5,'contenttypes','contenttype'),(11,'product','addon'),(12,'product','expressionhost'),(10,'product','expressionscale'),(18,'product','genesynenzymecutsite'),(9,'product','product'),(13,'product','purificationmethod'),(19,'product','species'),(14,'product','vector'),(6,'sessions','session'),(17,'tools','tool'),(22,'user_center','cart'),(21,'user_center','geneinfo'),(16,'user_center','order'),(20,'user_center','orderinfo'),(15,'user_center','shoppingcart');
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
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `django_migrations`
--

LOCK TABLES `django_migrations` WRITE;
/*!40000 ALTER TABLE `django_migrations` DISABLE KEYS */;
INSERT INTO `django_migrations` VALUES (1,'contenttypes','0001_initial','2023-10-23 06:13:17.041901'),(2,'auth','0001_initial','2023-10-23 06:13:17.218547'),(3,'account','0001_initial','2023-10-23 06:13:17.260536'),(4,'account','0002_userprofile','2023-10-23 06:13:17.303121'),(5,'admin','0001_initial','2023-10-23 06:13:17.362625'),(6,'admin','0002_logentry_remove_auto_add','2023-10-23 06:13:17.383930'),(7,'admin','0003_logentry_add_action_flag_choices','2023-10-23 06:13:17.422667'),(8,'contenttypes','0002_remove_content_type_name','2023-10-23 06:13:17.467694'),(9,'auth','0002_alter_permission_name_max_length','2023-10-23 06:13:17.498125'),(10,'auth','0003_alter_user_email_max_length','2023-10-23 06:13:17.533308'),(11,'auth','0004_alter_user_username_opts','2023-10-23 06:13:17.552539'),(12,'auth','0005_alter_user_last_login_null','2023-10-23 06:13:17.589948'),(13,'auth','0006_require_contenttypes_0002','2023-10-23 06:13:17.591928'),(14,'auth','0007_alter_validators_add_error_messages','2023-10-23 06:13:17.606367'),(15,'auth','0008_alter_user_username_max_length','2023-10-23 06:13:17.641127'),(16,'auth','0009_alter_user_last_name_max_length','2023-10-23 06:13:17.680963'),(17,'auth','0010_alter_group_name_max_length','2023-10-23 06:13:17.716401'),(18,'auth','0011_update_proxy_permissions','2023-10-23 06:13:17.734837'),(19,'auth','0012_alter_user_first_name_max_length','2023-10-23 06:13:17.772898'),(20,'product','0001_initial','2023-10-23 06:13:17.999846'),(21,'user_center','0001_initial','2023-10-23 06:13:18.218759'),(22,'product','0002_rename_expression_host_expressionhost_and_more','2023-10-23 06:13:18.553717'),(23,'product','0003_vector','2023-10-23 06:13:18.591482'),(24,'product','0004_delete_vector','2023-10-23 06:13:18.599513'),(25,'product','0005_vector','2023-10-23 06:13:18.643440'),(26,'product','0006_remove_vector_status_vector_is_ready_to_use','2023-10-23 06:13:18.699024'),(27,'sessions','0001_initial','2023-10-23 06:13:18.714708'),(28,'tools','0001_initial','2023-10-23 06:13:18.726925'),(29,'user_center','0002_alter_shoppingcart_express_host_and_more','2023-10-23 06:13:18.923103'),(30,'user_center','0003_alter_shoppingcart_status','2023-10-23 06:13:18.966994'),(31,'user_center','0004_alter_shoppingcart_project_name','2023-10-23 06:13:19.007174'),(32,'user_center','0005_alter_shoppingcart_status','2023-10-23 06:13:19.028903'),(33,'user_center','0006_shoppingcart_sequence_file','2023-10-23 06:13:19.065021'),(34,'tools','0002_tool_name_alias','2023-10-23 06:21:01.001030'),(35,'product','0007_remove_vector_c_gene_remove_vector_v_gene','2023-10-25 02:55:31.937805'),(36,'product','0008_alter_vector_vector_map','2023-10-25 02:57:10.077724'),(37,'product','0009_genesynenzymecutsite_remove_vector_cloning_site_and_more','2023-10-28 00:47:01.774624'),(38,'product','0010_alter_vector_nc3_alter_vector_nc5','2023-11-01 01:42:55.857945'),(39,'product','0011_vector_contained_forbidden_list_and_more','2023-11-01 02:07:54.489475'),(40,'product','0012_vector_gc_content','2023-11-01 07:54:07.068534'),(41,'product','0013_species','2023-11-02 10:36:27.310970'),(42,'user_center','0007_geneinfo_orderinfo_cart','2023-11-04 15:11:45.466079'),(43,'user_center','0008_alter_geneinfo_create_date','2023-11-04 16:11:35.730880'),(44,'user_center','0009_rename_gene_infos_cart_genes_delete_order','2023-11-07 10:22:26.515108'),(45,'user_center','0010_rename_origional_seq_geneinfo_original_seq','2023-11-16 05:52:20.922790'),(46,'product','0014_vector_id20_vector_iu20','2023-11-16 09:19:05.206721'),(47,'product','0015_remove_vector_contained_forbidden_list_and_more','2023-11-22 08:40:28.957576'),(48,'product','0016_alter_vector_vector_file','2023-11-22 09:03:59.556843');
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
INSERT INTO `django_session` VALUES ('0q49flylplj17m3wkiyft2eh9zs36fss','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r13bx:gUIVEdwZKNi1O8pCokvayQzJBOHYACm2qnZ8oV_RItM','2023-11-23 11:54:13.685055'),('343il2xv2m368ga0d1d2e6uz6exieiwg','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qvTpU:Wrl0rVgL1sQyL5acqKjCvhaYIRst0_zGAeD1xJ1BmOI','2023-11-08 02:41:08.399285'),('5u617oeetu9f4kyr60ldp4329tyi7avt','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r4Ztj:yp_kMh-6MW95AFkTwUvDSYT7AnD2qTtXuA8PnNK-ehQ','2023-12-03 04:59:07.682839'),('6e7x2hjzkmp2b6jqoibeip41s3krz575','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qxjI8:1Mvq22sgaFGTo4MEGbe7Fj0i1v8-MIyosXzTH_QKNMM','2023-11-14 07:36:00.977749'),('76lzdrorz1rzmbqma8n7dgtsbfdjj3zt','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qwWyM:AB0r5EY8fl-ULTBfR1fZ7yKaPOiIvJcPZz8EWBhM3ns','2023-11-11 00:14:38.936535'),('7fd5ydtebkmlnzwut0jo3x9hsigiuavf','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r3ZkG:_BP1kFdCS5ImhNDHG64GvcdRdvptopEMaGNqDnvryTY','2023-11-30 10:37:12.292123'),('83z6zv41jd3o7jok4zdguwxbq0lqyd9a','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r3Raz:1cM7oXy8E-6rOnGb2XnV35ajVeRCejd4RiprIqzWrEA','2023-11-30 01:55:05.544931'),('91rv0kw52yx4zyry6g0hkzmma083m2ro','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r3q7F:kjLERwzgMIhvh2JmX3xtS_vQ-jRMkpL_E7h5ECqWkxo','2023-12-01 04:06:01.582550'),('aa04hbktm6hb6kcxdomyjuvqyeann0r6','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qy04U:yjhbE9XhkzfoBwdItQbXh3VOjZApCeRtdeePeV-QKNs','2023-11-15 01:31:02.005636'),('bfgqhzxo9tqqi3dsfnmwk4jpcnlcxt5z','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzcPY:7GFvW05kg9F8qKVtKb62jfs01xAiol9Py18Gj5H_LvY','2023-11-19 12:39:28.758009'),('c26enbak9s8hrju6fl4nu0xa77q7gir7','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r50gX:2XWCdNP2_VBZEY_Yr6ibCF7aomPFRCwz2mZsrU1ztZ8','2023-12-04 09:35:17.487980'),('c2nvixv0c8pblab8jx1p7dv4si8t2vor','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r4glP:iaotgPUm78rNY1vdnRMmdsQo6FPtEVGMWgiekaLVBTM','2023-12-03 12:18:59.866951'),('c30gnt6fa5asmmd2v2028myhekn6qbgf','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r4uWP:FF7EosoI5bOqQEHEdqo5scAiyFhjsAWuqyrfrCaIiao','2023-12-04 03:00:25.591416'),('cbg1axnako2upor3ijpxh8bw75vkwk4u','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qxhya:e8ZMryoEg1UX6ODjY9TCQ_6xQ8UGAAkn4xkqAHIUrPg','2023-11-14 06:11:44.646267'),('gcvor56ggm0eekn86sf06wc9icgtilnv','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qyV4B:u-GBD5trZ_LRSAohpsI3tdz9WOfGnTPP7Z1peaMi2Nw','2023-11-16 10:36:47.282733'),('grdz2kc8uek8cwhesyll1iv9y2dzuhpl','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r5hXn:glhiDrjVmgy79lugndyVh5Wi0cUD6G17ELgBCpDuiYg','2023-12-06 07:21:07.659584'),('ictx3k6ilysk2ljnxsccpawsb36ofl2g','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzxYz:Sg-d3gT_71Np_qjGfA-_n0Jm2dTA1eOojHZjPr-gKKQ','2023-11-20 11:14:37.410023'),('j005muwxdkn2nr0dsivr39c04osin1zs','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r0GRo:JmUQxpdwoauxxnPtpAVPVakOdBi_3LMhjiwWS99pt_8','2023-11-21 07:24:28.187862'),('kitvu74jeo35e2vhsx42v2vtmdjgq28x','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzIVH:XfMvnZa1_ArVsp1X1wu13myByG6prZDl4Dg3y9ARj2c','2023-11-18 15:24:03.294490'),('kk95idpxcsndooz6tzarcgcud4a7l6kp','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r0tYX:wfI6XNxoffk9tcBBkJLtoBkEnNXEZShPtNL9Aq5PgBM','2023-11-23 01:10:01.582880'),('kmcxkis796s6grucmon5h6jxo25g8vir','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r3Zqy:hcVsA8sRNGbcNuXINjJy0HlcTMe7R0ybpKtAzep1IG4','2023-11-30 10:44:08.956184'),('l3qeyrost7b3cfui7u7fapzuf6yhlb3c','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qupll:q8D4iPFrIRTilY8OSu8RARmPYk19YpV2xlz_E5kF7Ls','2023-11-06 07:54:37.642283'),('mcqaifjs3ir270zbrsvpytiwp88lwmar','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qwHQc:4XVRsy7IkneLAQrxXEB_JRfS7XrYVk-1bmdTibI1CeA','2023-11-10 07:38:46.508042'),('nrz4d5cs8kship0w9c0ddtpdwlhqpssb','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzpj2:M0qE-lpM0dmk122482a1qAIgjpbpHeOPJ_ixPTNpx68','2023-11-20 02:52:28.610649'),('r7s2vr8n9mq9tr9m85rjcei0idrtcmu1','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r0MKw:AFH7acavL-a7JSm39tyg1flJDIncUAXNZa5OnyXtK64','2023-11-21 13:41:46.716798'),('sjllyr3hwm7q43ah5v9qr5kebuwzhz0y','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r1PIt:3pPW2Zm7sXNMaAtit1ONDQ6r457u_pZ_WrTo_iQjNOM','2023-11-24 11:03:59.385476'),('uxdkus9jnfi2dgus6ho2iz5a3yc0hc30','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qwXVb:AO5OX-lQZFXBWsr6BJSwhHKY-bpv9bcUhEbny4MAN5o','2023-11-11 00:48:59.564630'),('vd2wc7d03qrvncegp9mhopvcxham2bnb','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzB8j:ai50R_GrLUK7XLPK5GVMate6-K9I4uxsglGuRmsNGfs','2023-11-18 07:32:17.504855'),('w3gkqvblelprs5cmw3lcfxhsqu4pie2p','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r3Zmz:mEXX_hG6sDwX2FYmNCWMNfA4fLt3ehQbRxgEElsbVOU','2023-11-30 10:40:01.605112'),('w7sepczl2p3x5s89duu702q7frbhy1ru','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1quoG0:2BJ0lVr7AN59RcRLsobwsBBe6PtRwh89IgkEUai8kUw','2023-11-06 06:17:44.440396'),('wowm0ukkq1fiqruhsjbrjnp0hdiczy7t','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qwXaM:4Vt6UJjkZB2uUFmQRLYYiba6wb1xJabDgFRdxd3hps4','2023-11-11 00:53:54.864091'),('xwf8lnlylt43z8zb564t1ynjzfvxmgus','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qzc2l:8TNdsPy7AyCy48H2bwic5SeNhnC_lZe92rXwdC1f0NY','2023-11-19 12:15:55.287594'),('z28hqjtrqfa1g38kw3ofuywx5b2ixx4f','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1qxjzA:3e1ofQbcG2viyUw6LylIFnZrKAl_BBk2EuVIOqbozjc','2023-11-14 08:20:28.758383'),('z70av3gjx7vreq4y37b5t9yoe4fftmov','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1quoz5:RQkcEN7-LnkyBT7NtHnr6MxYw2Rc-wEn-7_5DJcrx5o','2023-11-06 07:04:19.348294'),('zhcrf1acnbpqdfj1serqp80b6k5vn1r5','.eJxVjEEOwiAQRe_C2pAyhTK4dN8zkAGmUjWQlHZlvLtt0oVu33v_v4Wnbc1-a7z4OYmrAHH5ZYHik8sh0oPKvcpYy7rMQR6JPG2TY038up3t30Gmlve1s0lBsMDR9sCstMKOMOGAhtWkAmobwEzY79RhF5xGS4Z1dFED8CA-X8uHNyk:1qy8L7:mEHGiqdiBcgXdZL7EJc4KF8DW-Qn0fIsvrEitF1vtKA','2023-11-15 10:20:45.373663'),('zsvm0gg8wck1qhjet6saaoruny7r9fr4','.eJxVjMEOwiAQRP-FsyHbFsvi0bvfQJZdKlUDSWlPxn-XJj3obTLvzbyVp21Nfqtx8bOoi-rU6bcLxM-YdyAPyveiueR1mYPeFX3Qqm9F4ut6uH8HiWpqawDsmHqCCUcj9gyud6aFEI0M1iFyb4k75kkYzIAwRMRRCLiF4Kz6fAHPOTep:1r2QjC:eDqxP5d8n-C0owhhSkOVl0aFWQfq44YZmTsnwruBZdY','2023-11-27 06:47:22.993056');
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
  `desc` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `turnaround_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_addon`
--

LOCK TABLES `product_addon` WRITE;
/*!40000 ALTER TABLE `product_addon` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_addon_product`
--

LOCK TABLES `product_addon_product` WRITE;
/*!40000 ALTER TABLE `product_addon_product` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionhost`
--

LOCK TABLES `product_expressionhost` WRITE;
/*!40000 ALTER TABLE `product_expressionhost` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionhost_product`
--

LOCK TABLES `product_expressionhost_product` WRITE;
/*!40000 ALTER TABLE `product_expressionhost_product` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionscale`
--

LOCK TABLES `product_expressionscale` WRITE;
/*!40000 ALTER TABLE `product_expressionscale` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_expressionscale_product`
--

LOCK TABLES `product_expressionscale_product` WRITE;
/*!40000 ALTER TABLE `product_expressionscale_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_expressionscale_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_genesynenzymecutsite`
--

DROP TABLE IF EXISTS `product_genesynenzymecutsite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_genesynenzymecutsite` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `enzyme_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `enzyme_seq` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `usescope` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_genesynenzymecutsite`
--

LOCK TABLES `product_genesynenzymecutsite` WRITE;
/*!40000 ALTER TABLE `product_genesynenzymecutsite` DISABLE KEYS */;
INSERT INTO `product_genesynenzymecutsite` VALUES (1,'BsmBI-R','GAGACG','2500-5000'),(2,'BsmBI-F','CGTCTC','2500-5000'),(3,'BbsI-R','GTCTTC','500-5000'),(4,'BbsI-F','GAAGAC','500-5000'),(5,'BsaI-R','GAGACC','0-5000'),(6,'BsaI-F','GGTCTC','0-5000');
/*!40000 ALTER TABLE `product_genesynenzymecutsite` ENABLE KEYS */;
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
  `product_name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `price` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `turnaround_time` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_product`
--

LOCK TABLES `product_product` WRITE;
/*!40000 ALTER TABLE `product_product` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_purificationmethod`
--

LOCK TABLES `product_purificationmethod` WRITE;
/*!40000 ALTER TABLE `product_purificationmethod` DISABLE KEYS */;
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_purificationmethod_product`
--

LOCK TABLES `product_purificationmethod_product` WRITE;
/*!40000 ALTER TABLE `product_purificationmethod_product` DISABLE KEYS */;
/*!40000 ALTER TABLE `product_purificationmethod_product` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_species`
--

DROP TABLE IF EXISTS `product_species`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_species` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `species_name` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  `species_note` varchar(256) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_species`
--

LOCK TABLES `product_species` WRITE;
/*!40000 ALTER TABLE `product_species` DISABLE KEYS */;
INSERT INTO `product_species` VALUES (1,'Arabidopsis','Arabidopsis'),(2,'CHO','CHO'),(3,'Drosophila','Drosophila'),(4,'Human','Human'),(5,'Insect','Insect'),(6,'Maize','Maize'),(7,'Mouse','Mouse'),(8,'Pig','Pig'),(9,'Rat','Rat'),(10,'Tabacco','Tabacco'),(11,'Yeast','Yeast'),(12,'Streptomyces','Streptomyces'),(13,'C_elegans','C_elegans'),(14,'E_coli','E_coli'),(15,'Pichia_pastoris','Pichia_pastoris'),(16,'Saccharomyces_cerevisiae','Saccharomyces_cerevisiae');
/*!40000 ALTER TABLE `product_species` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `product_vector`
--

DROP TABLE IF EXISTS `product_vector`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `product_vector` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vector_name` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `vector_map` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `NC5` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `NC3` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int DEFAULT NULL,
  `combined_seq` longtext COLLATE utf8mb4_unicode_ci,
  `create_date` datetime(6) NOT NULL,
  `saved_seq` longtext COLLATE utf8mb4_unicode_ci,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `id20` longtext COLLATE utf8mb4_unicode_ci,
  `iu20` longtext COLLATE utf8mb4_unicode_ci,
  `vector_file` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `product_vector_user_id_f5718aa6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `product_vector_user_id_f5718aa6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `product_vector`
--

LOCK TABLES `product_vector` WRITE;
/*!40000 ALTER TABLE `product_vector` DISABLE KEYS */;
INSERT INTO `product_vector` VALUES (1,'pUC19','CTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACGCGCGGGGAGAGGCGGTTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGtGAtCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTAATTGTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCTTGCCCGGCGTCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATACTCTTCCTTTTTCAATATTATTGAAGCATTTATCAGGGTTATTGTCTCATGAGCGGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGGGGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGTCTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAGGCGTATCACGAGGCCCTTTCGTCTCGCGCGTTTCGGTGATGACGGTGAAAACCTCTGACACATGCAGCTCCCGGAGACGGTCACAGCTTGTCTGTAAGCGGATGCCGGGAGCAGACAAGCCCGTCAGGGCGCGTCAGCGGGTGTTGGCGGGTGTCGGGGCTGGCTTAACTATGCGGCATCAGAGCAGATTGTACTGAGAGTGCACCATATGCGGTGTGAAATACCGCACAGATGCGTAAGGAGAAAATACCGCATCAGGCGCCATTCGCCATTCAGGCTGCGCAACTGTTGGGAAGGGCGATCGGTGCGGGCCTCTTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACG','TTGTAAAACGACGGCCAGTG','GCTTGGCGTAATCATGGTCA',NULL,'','2023-10-28 00:47:01.000000','','ReadyToUse',NULL,NULL,NULL),(14,'vector1','GCTTGGCGTAATCATGGTCATAG','TTGTAAAACGACGGCCAGTG','CTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACGCGCGGGGAGAGGCGGTTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGtGAtCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTAATTGTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCTTGCCCGGCGTCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATACTCTTCCTTTTTCAATATTATTGAAGCATTTATCAGGGTTATTGTCTCATGAGCGGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGGGGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGTCTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAGGCGTATCACGAGGCCCTTTCGTCTCGCGCGTTTCGGTGATGACGGTGAAAACCTCTGACACATGCAGCTCCCGGAGACGGTCACAGCTTGTCTGTAAGCGGATGCCGGGAGCAGACAAGCCCGTCAGGGCGCGTCAGCGGGTGTTGGCGGGTGTCGGGGCTGGCTTAACTATGCGGCATCAGAGCAGATTGTACTGAGAGTGCACCATATGCGGTGTGAAATACCGCACAGATGCGTAAGGAGAAAATACCGCATCAGGCGCCATTCGCCATTCAGGCTGCGCAACTGTTGGGAAGGGCGATCGGTGCGGGCCTCTTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACG',2,'TTGTAAAACGACGGCCAGTGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAA<em class=\"text-warning\">TCGGCCAACGCGCGGGGAGAGGCGG</em>TTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGG<em class=\"text-warning\">TCGTTCGGCTGCGGCGAGCGG</em>TATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCAT<em class=\"text-warning\">AGGCTCCGCCCCCCTGACGAGC</em>ATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGA<em class=\"text-warning\">ACCCCCCGTTCAGCCCGACCGC</em>TGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCA<em class=\"text-warning\">CCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTT</em>GGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGTGATCCACGCTCACCGGCTCCAGATTTATCAGCAATAA<em class=\"text-warning\">ACCAGCCAGCCGGAAGGGCCGAGCGCAG</em>AAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGT<em class=\"text-warning\">CTATTAATT</em>GTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCT<em class=\"text-warning\">TGCCCGGCG</em>TCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATA<em class=\"text-warning\">CTCTTCCTTTTTCAATATTATTGAAGCATTTATCA</em>GGGTTATTGTCTCATGAGC<em class=\"text-warning\">GGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGG</em>GGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGT<em class=\"text-warning\">CTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAG</em>GCGTATCACGAGGCCCTT<span class=\"bg-danger\">TCGTCTC</span>GCGCGTTTCGGTGATGACGGTGAAAACCTCTGACACATGCAGCTCCC<span class=\"bg-danger\">GGAGACG</span>GTCACAGCTTGTCTGTAAGCGGATGCCGGGAGCAGACA<em class=\"text-warning\">AGCCCGTCAGGGCGCGTCAGCGGG</em>TG<em class=\"text-warning\">TTGGCGGGTGTCGGGGCTGGCT</em>TAACTATGCGGCATCAGAGCAGATTGTACTGAGAGTGCACCATATGCGGTGTGAAATACCGCACAGATGCGTAAGGAGAAAATACCGCATCAGGCGCCATTCGCCATTCAGGCTGCGCAACTGTTGGGA<em class=\"text-warning\">AGGGCGATCGGTGCGGGCCTC</em>TTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACGGCTTGGCGTAATCATGGTCATAG','2023-11-01 10:24:48.183790','TTGTAAAACGACGGCCAGTGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAA<em class=\"text-warning\">TCGGCCAACGCGCGGGGAGAGGCGG</em>TTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGG<em class=\"text-warning\">TCGTTCGGCTGCGGCGAGCGG</em>TATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCAT<em class=\"text-warning\">AGGCTCCGCCCCCCTGACGAGC</em>ATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGA<em class=\"text-warning\">ACCCCCCGTTCAGCCCGACCGC</em>TGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCA<em class=\"text-warning\">CCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTT</em>GGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGTGATCCACGCTCACCGGCTCCAGATTTATCAGCAATAA<em class=\"text-warning\">ACCAGCCAGCCGGAAGGGCCGAGCGCAG</em>AAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGT<em class=\"text-warning\">CTATTAATT</em>GTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCT<em class=\"text-warning\">TGCCCGGCG</em>TCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATA<em class=\"text-warning\">CTCTTCCTTTTTCAATATTATTGAAGCATTTATCA</em>GGGTTATTGTCTCATGAGC<em class=\"text-warning\">GGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGG</em>GGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGT<em class=\"text-warning\">CTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAG</em>GCGTATCACGAGGCCCTT<span class=\"bg-danger\">TCGTCTC</span>GCGCGTTTCGGTGATGACGGTGAAAACCTCTGACACATGCAGCTCCC<span class=\"bg-danger\">GGAGACG</span>GTCACAGCTTGTCTGTAAGCGGATGCCGGGAGCAGACA<em class=\"text-warning\">AGCCCGTCAGGGCGCGTCAGCGGG</em>TG<em class=\"text-warning\">TTGGCGGGTGTCGGGGCTGGCT</em>TAACTATGCGGCATCAGAGCAGATTGTACTGAGAGTGCACCATATGCGGTGTGAAATACCGCACAGATGCGTAAGGAGAAAATACCGCATCAGGCGCCATTCGCCATTCAGGCTGCGCAACTGTTGGGA<em class=\"text-warning\">AGGGCGATCGGTGCGGGCCTC</em>TTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACGGCTTGGCGTAATCATGGTCATAG','forbidden',NULL,NULL,NULL),(18,'pcDNA3.4','attacaaaatttgtgaaagattgactggtattcttaactatgttgctccttttacgctatgtggatacgctgctttaatgcctttgtatcatgctattgcttcccgtatggctttcattttctcctccttgtataaatcctggttgctgtctctttatgaggagttgtggcccgttgtcaggcaacgtggcgtggtgtgcactgtgtttgctgacgcaacccccactggttggggcattgccaccacctgtcagctcctttccgggactttcgctttccccctccctattgccacggcggaactcatcgccgcctgccttgcccgctgctggacaggggctcggctgttgggcactgacaattccgtggtgttgtcggggaagctgacgtcctttccatggctgctcgcctgtgttgccacctggattctgcgcgggacgtccttctgctacgtcccttcggccctcaatccagcggaccttccttcccgcggcctgctgccggctctgcggcctcttccgcgtcttcgccttcgccctcagacgagtcggatctccctttgggccgcctccccgcctggctagagggcccgtttaaacaagggttcgatccctaccggttagtaatgagtttaaacgggggaggctaactgaaacacggaaggagacaataccggaaggaacccgcgctatgacggcaataaaaagacagaataaaacgcacgggtgttgggtcgtttgttcataaacgcggggttcggtcccagggctggcactctgtcgataccccaccgagaccccattggggccaatacgcccgcgtttcttccttttccccaccccaccccccaagttcgggtgaaggcccagggctcgcagccaacgtcggggcggcaggccctgccatagcagatctgcgcagctggggctctagggggtatccccacgcgccctgtagcggcgcattaagcgcggcgggtgtggtggttacgcgcagcgtgaccgctacacttgccagcgccctagcgcccgctcctttcgctttcttcccttcctttctcgccacgttcgccggctttccccgtcaagctctaaatcggggcatccctttagggttccgatttagtgctttacggcacctcgaccccaaaaaacttgattagggtgatggttcacgtagtgggccatcgccctgatagacggtttttcgccctttgacgttggagtccacgttctttaatagtggactcttgttccaaactggaacaacactcaaccctatctcggtctattcttttgatttataagggattttggggatttcggcctattggttaaaaaatgagctgatttaacaaaaatttaacgcgaattaattctgtggaatgtgtgtcagttagggtgtggaaagtccccaggctccccagcaggcagaagtatgcaaagcatgcatctcaattagtcagcaaccaggtgtggaaagtccccaggctccccagcaggcagaagtatgcaaagcatgcatctcaattagtcagcaaccatagtcccgcccctaactccgcccatcccgcccctaactccgcccagttccgcccattctccgccccatggctgactaattttttttatttatgcagaggccgaggccgcctctgcctctgagctattccagaagtagtgaggaggcttttttggaggcctaggcttttgcaaaaagctcccgggagcttgtatatccattttcggatctgatcaagagacaggatgaggatcgtttcgcatgattgaacaagatggattgcacgcaggttctccggccgcttgggtggagaggctattcggctatgactgggcacaacagacaatcggctgctctgatgccgccgtgttccggctgtcagcgcaggggcgcccggttctttttgtcaagaccgacctgtccggtgccctgaatgaactgcaggacgaggcagcgcggctatcgtggctggccacgacgggcgttccttgcgcagctgtgctcgacgttgtcactgaagcgggaagggactggctgctattgggcgaagtgccggggcaggatctcctgtcatctcaccttgctcctgccgagaaagtatccatcatggctgatgcaatgcggcggctgcatacgcttgatccggctacctgcccattcgaccaccaagcgaaacatcgcatcgagcgagcacgtactcggatggaagccggtcttgtcgatcaggatgatctggacgaagagcatcaggggctcgcgccagccgaactgttcgccaggctcaaggcgcgcatgcccgacggcgaggatctcgtcgtgacccatggcgatgcctgcttgccgaatatcatggtggaaaatggccgcttttctggattcatcgactgtggccggctgggtgtggcggaccgctatcaggacatagcgttggctacccgtgatattgctgaagagcttggcggcgaatgggctgaccgcttcctcgtgctttacggtatcgccgctcccgattcgcagcgcatcgccttctatcgccttcttgacgagttcttctgagcgggactctggggttcgcgaaatgaccgaccaagcgacgcccaacctgccatcacgagatttcgattccaccgccgccttctatgaaaggttgggcttcggaatcgttttccgggacgccggctggatgatcctccagcgcggggatctcatgctggagttcttcgcccaccccaacttgtttattgcagcttataatggttacaaataaagcaatagcatcacaaatttcacaaataaagcatttttttcactgcattctagttgtggtttgtccaaactcatcaatgtatcttatcatgtctgtataccgtcgacctctagctagagcttggcgtaatcatggtcatagctgtttcctgtgtgaaattgttatccgctcacaattccacacaacatacgagccggaagcataaagtgtaaagcctggggtgcctaatgagtgagctaactcacattaattgcgttgcgctcactgcccgctttccagtcgggaaacctgtcgtgccagctgcattaatgaatcggccaacgcgcggggagaggcggtttgcgtattgggcgctcttccgcttcctcgctcactgactcgctgcgctcggtcgttcggctgcggcgagcggtatcagctcactcaaaggcggtaatacggttatccacagaatcaggggataacgcaggaaagaacatgtgagcaaaaggccagcaaaaggccaggaaccgtaaaaaggccgcgttgctggcgtttttccataggctccgcccccctgacgagcatcacaaaaatcgacgctcaagtcagaggtggcgaaacccgacaggactataaagataccaggcgtttccccctggaagctccctcgtgcgctctcctgttccgaccctgccgcttaccggatacctgtccgcctttctcccttcgggaagcgtggcgctttctcaatgctcacgctgtaggtatctcagttcggtgtaggtcgttcgctccaagctgggctgtgtgcacgaaccccccgttcagcccgaccgctgcgccttatccggtaactatcgtcttgagtccaacccggtaagacacgacttatcgccactggcagcagccactggtaacaggattagcagagcgaggtatgtaggcggtgctacagagttcttgaagtggtggcctaactacggctacactagaaggacagtatttggtatctgcgctctgctgaagccagttaccttcggaaaaagagttggtagctcttgatccggcaaacaaaccaccgctggtagcggtggtttttttgtttgcaagcagcagattacgcgcagaaaaaaaggatctcaagaagatcctttgatcttttctacggggtctgacgctcagtggaacgaaaactcacgttaagggattttggtcatgagattatcaaaaaggatcttcacctagatccttttaaattaaaaatgaagttttaaatcaatctaaagtatatatgagtaaacttggtctgacagttaccaatgcttaatcagtgaggcacctatctcagcgatctgtctatttcgttcatccatagttgcctgactccccgtcgtgtagataactacgatacgggagggcttaccatctggccccagtgctgcaatgataccgcgagacccacgctcaccggctccagatttatcagcaataaaccagccagccggaagggccgagcgcagaagtggtcctgcaactttatccgcctccatccagtctattaattgttgccgggaagctagagtaagtagttcgccagttaatagtttgcgcaacgttgttgccattgctacaggcatcgtggtgtcacgctcgtcgtttggtatggcttcattcagctccggttcccaacgatcaaggcgagttacatgatcccccatgttgtgcaaaaaagcggttagctccttcggtcctccgatcgttgtcagaagtaagttggccgcagtgttatcactcatggttatggcagcactgcataattctcttactgtcatgccatccgtaagatgcttttctgtgactggtgagtactcaaccaagtcattctgagaatagtgtatgcggcgaccgagttgctcttgcccggcgtcaatacgggataataccgcgccacatagcagaactttaaaagtgctcatcattggaaaacgttcttcggggcgaaaactctcaaggatcttaccgctgttgagatccagttcgatgtaacccactcgtgcacccaactgatcttcagcatcttttactttcaccagcgtttctgggtgagcaaaaacaggaaggcaaaatgccgcaaaaaagggaataagggcgacacggaaatgttgaatactcatactcttcctttttcaatattattgaagcatttatcagggttattgtctcatgagcggatacatatttgaatgtatttagaaaaataaacaaataggggttccgcgcacatttccccgaaaagtgccacctgacgtcgacggatcgggagatctcccgatcccctatggtcgactctcagtacaatctgctctgatgccgcatagttaagccagtatctgctccctgcttgtgtgttggaggtcgctgagtagtgcgcgagcaaaatttaagctacaacaaggcaaggcttgaccgacaattgcatgaagaatctgcttagggttaggcgttttgcgctgcttcgcgatgtacgggccagatatacgcgttgacattgattattgactagttattaatagtaatcaattacggggtcattagttcatagcccatatatggagttccgcgttacataacttacggtaaatggcccgcctggctgaccgcccaacgacccccgcccattgacgtcaataatgacgtatgttcccatagtaacgccaatagggactttccattgacgtcaatgggtggagtatttacggtaaactgcccacttggcagtacatcaagtgtatcatatgccaagtacgccccctattgacgtcaatgacggtaaatggcccgcctggcattatgcccagtacatgaccttatgggactttcctacttggcagtacatctacgtattagtcatcgctattaccatggtgatgcggttttggcagtacatcaatgggcgtggatagcggtttgactcacggggatttccaagtctccaccccattgacgtcaatgggagtttgttttggcaccaaaatcaacgggactttccaaaatgtcgtaacaactccgccccattgacgcaaatgggcggtaggcgtgtacggtgggaggtctatataagcagagctcgtttagtgaaccgtcagatcgcctgCTgacgccatccacgctgttttgacctccatagaagacacc','gggaccgatccagcct','tagagtcgacaatcaacctctgg',NULL,'','2023-11-05 13:17:37.000000','','ReadyToUse',NULL,NULL,NULL),(19,'pET11a','ccgaaaggaagctgagttggctgctgccaccgctgagcaataactagcataaccccttggggcctctaaacgggtcttgaggggttttttgctgaaaggaggaactatatccggatatcccgcaagaggcccggcagtaccggcataaccaagcctatgcctacagcatccagggtgacggtgccgaggatgacgatgagcgcattgttagatttcatacacggtgcctgactgcgttagcaatttaactgtgataaactaccgcattaaagcttatcgatgataagctgtcaaacatgagaattcttgaagacgaaagggcctcgtgatacgcctatttttataggttaatgtcatgataataatggtttcttagacgtcaggtggcacttttcggggaaatgtgcgcggaacccctatttgtttatttttctaaatacattcaaatatgtatccgctcatgagacaataaccctgataaatgcttcaataatattgaaaaaggaagagtatgagtattcaacatttccgtgtcgcccttattcccttttttgcggcattttgccttcctgtttttgctcacccagaaacgctggtgaaagtaaaagatgctgaagatcagttgggtgcacgagtgggttacatcgaactggatctcaacagcggtaagatccttgagagttttcgccccgaagaacgttttccaatgatgagcacttttaaagttctgctatgtggcgcggtattatcccgtgttgacgccgggcaagagcaactcggtcgccgcatacactattctcagaatgacttggttgagtactcaccagtcacagaaaagcatcttacggatggcatgacagtaagagaattatgcagtgctgccataaccatgagtgataacactgcggccaacttacttctgacaacgatcggaggaccgaaggagctaaccgcttttttgcacaacatgggggatcatgtaactcgccttgatcgttgggaaccggagctgaatgaagccataccaaacgacgagcgtgacaccacgatgcctgcagcaatggcaacaacgttgcgcaaactattaactggcgaactacttactctagcttcccggcaacaattaatagactggatggaggcggataaagttgcaggaccacttctgcgctcggcccttccggctggctggtttattgctgataaatctggagccggtgagcgtgGaTCaCgcggtatcattgcagcactggggccagatggtaagccctcccgtatcgtagttatctacacgacggggagtcaggcaactatggatgaacgaaatagacagatcgctgagataggtgcctcactgattaagcattggtaactgtcagaccaagtttactcatatatactttagattgatttaaaacttcatttttaatttaaaaggatctaggtgaagatcctttttgataatctcatgaccaaaatcccttaacgtgagttttcgttccactgagcgtcagaccccgtagaaaagatcaaaggatcttcttgagatcctttttttctgcgcgtaatctgctgcttgcaaacaaaaaaaccaccgctaccagcggtggtttgtttgccggatcaagagctaccaactctttttccgaaggtaactggcttcagcagagcgcagataccaaatactgtccttctagtgtagccgtagttaggccaccacttcaagaactctgtagcaccgcctacatacctcgctctgctaatcctgttaccagtggctgctgccagtggcgataagtcgtgtcttaccgggttggactcaagacgatagttaccggataaggcgcagcggtcgggctgaacggggggttcgtgcacacagcccagcttggagcgaacgacctacaccgaactgagatacctacagcgtgagctatgagaaagcgccacgcttcccgaagggagaaaggcggacaggtatccggtaagcggcagggtcggaacaggagagcgcacgagggagcttccagggggaaacgcctggtatctttatagtcctgtcgggtttcgccacctctgacttgagcgtcgatttttgtgatgctcgtcaggggggcggagcctatggaaaaacgccagcaacgcggcctttttacggttcctggccttttgctggccttttgctcacatgttctttcctgcgttatcccctgattctgtggataaccgtattaccgcctttgagtgagctgataccgctcgccgcagccgaacgaccgagcgcagcgagtcagtgagcgaggaagcggaagagcgcctgatgcggtattttctccttacgcatctgtgcggtatttcacaccgcatatatggtgcactctcagtacaatctgctctgatgccgcatagttaagccagtatacactccgctatcgctacgtgactgggtcatggctgcgccccgacacccgccaacacccgctgacgcgccctgacgggcttgtctgctcccggcatccgcttacagacaagctgtgaccgtctccgggagctgcatgtgtcagaggttttcaccgtcatcaccgaaacgcgcgaggcagctgcggtaaagctcatcagcgtggtcgtgaagcgattcacagatgtctgcctgttcatccgcgtccagctcgttgagtttctccagaagcgttaatgtctggcttctgataaagcgggccatgttaagggcggttttttcctgtttggtcactgatgcctccgtgtaagggggatttctgttcatgggggtaatgataccgatgaaacgagagaggatgctcacgatacgggttactgatgatgaacatgcccggttactggaacgttgtgagggtaaacaactggcggtatggatgcggcgggaccagagaaaaatcactcagggtcaatgccagcgcttcgttaatacagatgtaggtgttccacagggtagccagcagcatcctgcgatgcagatccggaacataatggtgcagggcgctgacttccgcgtttccagactttacgaaacacggaaaccgaagaccattcatgttgttgctcaggtcgcagacgttttgcagcagcagtcgcttcacgttcgctcgcgtatcggtgattcattctgctaaccagtaaggcaaccccgccagcctagccgggtcctcaacgacaggagcacgatcatgcgcacccgtggccaggacccaacgctgcccgagatgcgccgcgtgcggctgctggagatggcggacgcgatggatatgttctgccaagggttggtttgcgcattcacagttctccgcaagaattgattggctccaattcttggagtggtgaatccgttagcgaggtgccgccggcttccattcaggtcgaggtggcccggctccatgcaccgcgacgcaacgcggggaggcagacaaggtatagggcggcgcctacaatccatgccaacccgttccatgtgctcgccgaggcggcataaatcgccgtgacgatcagcggtccagtgatcgaagttaggctggtaagagccgcgagcgatccttgaagctgtccctgatggtcgtcatctacctgcctggacagcatggcctgcaacgcgggcatcccgatgccgccggaagcgagaagaatcataatggggaaggccatccagcctcgcgtcgcgaacgccagcaagacgtagcccagcgcgtcggccgccatgccggcgataatggcctgcttctcgccgaaacgtttggtggcgggaccagtgacgaaggcttgagcgagggcgtgcaagattccgaataccgcaagcgacaggccgatcatcgtcgcgctccagcgaaagcggtcctcgccgaaaatgacccagagcgctgccggcacctgtcctacgagttgcatgataaagaagacagtcataagtgcggcgacgatagtcatgccccgcgcccaccggaaggagctgactgggttgaaggctctcaagggcatcggtcgagatcccggtgcctaatgagtgagctaacttacattaattgcgttgcgctcactgcccgctttccagtcgggaaacctgtcgtgccagctgcattaatgaatcggccaacgcgcggggagaggcggtttgcgtattgggcgccagggtggtttttcttttcaccagtgagacgggcaacagctgattgcccttcaccgcctggccctgagagagttgcagcaagcggtccacgctggtttgccccagcaggcgaaaatcctgtttgatggtggttaacggcgggatataacatgagctgtcttcggtatcgtcgtatcccactaccgagatatccgcaccaacgcgcagcccggactcggtaatggcgcgcattgcgcccagcgccatctgatcgttggcaaccagcatcgcagtgggaacgatgccctcattcagcatttgcatggtttgttgaaaaccggacatggcactccagtcgccttcccgttccgctatcggctgaatttgattgcgagtgagatatttatgccagccagccagacgcagacgcgccgagacagaacttaatgggcccgctaacagcgcgatttgctggtgacccaatgcgaccagatgctccacgcccagtcgcgtaccgtcttcatgggagaaaataatactgttgatgggtgtctggtcagagacatcaagaaataacgccggaacattagtgcaggcagcttccacagcaatggcatcctggtcatccagcggatagttaatgatcagcccactgacgcgttgcgcgagaagattgtgcaccgccgctttacaggcttcgacgccgcttcgttctaccatcgacaccaccacgctggcacccagttgatcggcgcgagatttaatcgccgcgacaatttgcgacggcgcgtgcagggccagactggaggtggcaacgccaatcagcaacgactgtttgcccgccagttgttgtgccacgcggttgggaatgtaattcagctccgccatcgccgcttccactttttcccgcgttttcgcagaaacgtggctggcctggttcaccacgcgggaaacggtctgataagagacaccggcatactctgcgacatcgtataacgttactggtttcacattcaccaccctgaattgactctcttccgggcgctatcatgccataccgcgaaaggttttgcgccattcgatggtgtccgggatctcgacgctctcccttatgcgactcctgcattaggaagcagcccagtagtaggttgaggccgttgagcaccgccgccgcaaggaatggtgcatgcaaggagatggcgcccaacagtcccccggccacggggcctgccaccatacccacgccgaaacaagcgctcatgagcccgaagtggcgagcccgatcttccccatcggtgatgtcggcgatataggcgccagcaaccgcacctgtggcgccggtgatgccggccacgatgcgtccggcgtagaggatcgagatctcgatcccgcgaaattaatacgactcactataggggaattgtgagcggataacaattcccctctagaaataattttgt','ttaactttaagaaggagatatacat','cggctgctaacaaagc',NULL,'','2023-11-05 13:20:05.000000','','ReadyToUse',NULL,NULL,NULL),(20,'pUC19v2','GCTTGGCGTAATCATGGTCATAGCTGTTTCCTGTGTGAAATTGTTATCCGCTCACAATTCCACACAACATACGAGCCGGAAGCATAAAGTGTAAAGCCTGGGGTGCCTAATGAGTGAGCTAACTCACATTAATTGCGTTGCGCTCACTGCCCGCTTTCCAGTCGGGAAACCTGTCGTGCCAGCTGCATTAATGAATCGGCCAACGCGCGGGGAGAGGCGGTTTGCGTATTGGGCGCTCTTCCGCTTCCTCGCTCACTGACTCGCTGCGCTCGGTCGTTCGGCTGCGGCGAGCGGTATCAGCTCACTCAAAGGCGGTAATACGGTTATCCACAGAATCAGGGGATAACGCAGGAAAGAACATGTGAGCAAAAGGCCAGCAAAAGGCCAGGAACCGTAAAAAGGCCGCGTTGCTGGCGTTTTTCCATAGGCTCCGCCCCCCTGACGAGCATCACAAAAATCGACGCTCAAGTCAGAGGTGGCGAAACCCGACAGGACTATAAAGATACCAGGCGTTTCCCCCTGGAAGCTCCCTCGTGCGCTCTCCTGTTCCGACCCTGCCGCTTACCGGATACCTGTCCGCCTTTCTCCCTTCGGGAAGCGTGGCGCTTTCTCATAGCTCACGCTGTAGGTATCTCAGTTCGGTGTAGGTCGTTCGCTCCAAGCTGGGCTGTGTGCACGAACCCCCCGTTCAGCCCGACCGCTGCGCCTTATCCGGTAACTATCGTCTTGAGTCCAACCCGGTAAGACACGACTTATCGCCACTGGCAGCAGCCACTGGTAACAGGATTAGCAGAGCGAGGTATGTAGGCGGTGCTACAGAGTTCTTGAAGTGGTGGCCTAACTACGGCTACACTAGAAGAACAGTATTTGGTATCTGCGCTCTGCTGAAGCCAGTTACCTTCGGAAAAAGAGTTGGTAGCTCTTGATCCGGCAAACAAACCACCGCTGGTAGCGGTGGTTTTTTTGTTTGCAAGCAGCAGATTACGCGCAGAAAAAAAGGATCTCAAGAAGATCCTTTGATCTTTTCTACGGGGTCTGACGCTCAGTGGAACGAAAACTCACGTTAAGGGATTTTGGTCATGAGATTATCAAAAAGGATCTTCACCTAGATCCTTTTAAATTAAAAATGAAGTTTTAAATCAATCTAAAGTATATATGAGTAAACTTGGTCTGACAGTTACCAATGCTTAATCAGTGAGGCACCTATCTCAGCGATCTGTCTATTTCGTTCATCCATAGTTGCCTGACTCCCCGTCGTGTAGATAACTACGATACGGGAGGGCTTACCATCTGGCCCCAGTGCTGCAATGATACCGCGAGACCCACGCTCACCGGCTCCAGATTTATCAGCAATAAACCAGCCAGCCGGAAGGGCCGAGCGCAGAAGTGGTCCTGCAACTTTATCCGCCTCCATCCAGTCTATTAATTGTTGCCGGGAAGCTAGAGTAAGTAGTTCGCCAGTTAATAGTTTGCGCAACGTTGTTGCCATTGCTACAGGCATCGTGGTGTCACGCTCGTCGTTTGGTATGGCTTCATTCAGCTCCGGTTCCCAACGATCAAGGCGAGTTACATGATCCCCCATGTTGTGCAAAAAAGCGGTTAGCTCCTTCGGTCCTCCGATCGTTGTCAGAAGTAAGTTGGCCGCAGTGTTATCACTCATGGTTATGGCAGCACTGCATAATTCTCTTACTGTCATGCCATCCGTAAGATGCTTTTCTGTGACTGGTGAGTACTCAACCAAGTCATTCTGAGAATAGTGTATGCGGCGACCGAGTTGCTCTTGCCCGGCGTCAATACGGGATAATACCGCGCCACATAGCAGAACTTTAAAAGTGCTCATCATTGGAAAACGTTCTTCGGGGCGAAAACTCTCAAGGATCTTACCGCTGTTGAGATCCAGTTCGATGTAACCCACTCGTGCACCCAACTGATCTTCAGCATCTTTTACTTTCACCAGCGTTTCTGGGTGAGCAAAAACAGGAAGGCAAAATGCCGCAAAAAAGGGAATAAGGGCGACACGGAAATGTTGAATACTCATACTCTTCCTTTTTCAATATTATTGAAGCATTTATCAGGGTTATTGTCTCATGAGCGGATACATATTTGAATGTATTTAGAAAAATAAACAAATAGGGGTTCCGCGCACATTTCCCCGAAAAGTGCCACCTGACGTCTAAGAAACCATTATTATCATGACATTAACCTATAAAAATAGGCGTATCACGAGGCCCTTTCGaCTCGCGCGTTTCGGTGATGACGGTGAAAACCTCTGACACATGCAGCTCCCGGAGACtGTCACAGCTTGTCTGTAAGCGGATGCCGGGAGCAGACAAGCCCGTCAGGGCGCGTCAGCGGGTGTTGGCGGGTGTCGGGGCTGGCTTAACTATGCGGCATCAGAGCAGATTGTACTGAGAGTGCACCATATGCGGTGTGAAATACCGCACAGATGCGTAAGGAGAAAATACCGCATCAGGCGCCATTCGCCATTCAGGCTGCGCAACTGTTGGGAAGGGCGATCGGTGCGGGCCTCTTCGCTATTACGCCAGCTGGCGAAAGGGGGATGTGCTGCAAGGCGATTAAGTTGGGTAACGCCAGGGTTTTCCCAGTCACGACGTTGTAAAACGACGGCCAGTG','TTGTAAAACGACGGCCAGTG','GCTTGGCGTAATCATGGTCATAG',NULL,'','2023-11-05 13:20:52.000000','','ReadyToUse',NULL,NULL,NULL);
/*!40000 ALTER TABLE `product_vector` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tools_tool`
--

DROP TABLE IF EXISTS `tools_tool`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tools_tool` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tool_name` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tool_desc` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `tool_freq` smallint NOT NULL,
  `tool_icon` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name_alias` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tools_tool`
--

LOCK TABLES `tools_tool` WRITE;
/*!40000 ALTER TABLE `tools_tool` DISABLE KEYS */;
INSERT INTO `tools_tool` VALUES (1,'SequenceAnalyzer','Helps users analyze sequences to detect anomalies or errors.',0,'','Sequence Analyzer');
/*!40000 ALTER TABLE `tools_tool` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_cart`
--

DROP TABLE IF EXISTS `user_center_cart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_cart` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `created_at` datetime(6) NOT NULL,
  `updated_at` datetime(6) NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_center_cart_user_id_c45a266c_fk_auth_user_id` (`user_id`),
  CONSTRAINT `user_center_cart_user_id_c45a266c_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_cart`
--

LOCK TABLES `user_center_cart` WRITE;
/*!40000 ALTER TABLE `user_center_cart` DISABLE KEYS */;
INSERT INTO `user_center_cart` VALUES (1,'2023-11-07 10:21:23.947680','2023-11-21 02:01:59.520014',1),(2,'2023-11-09 11:00:34.372504','2023-11-15 10:06:18.895255',3),(3,'2023-11-09 11:03:15.663148','2023-11-09 11:03:15.663216',4);
/*!40000 ALTER TABLE `user_center_cart` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_cart_genes`
--

DROP TABLE IF EXISTS `user_center_cart_genes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_cart_genes` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cart_id` bigint NOT NULL,
  `geneinfo_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_center_cart_gene_infos_cart_id_geneinfo_id_6d316a4e_uniq` (`cart_id`,`geneinfo_id`),
  KEY `user_center_cart_gen_geneinfo_id_677d2edc_fk_user_cent` (`geneinfo_id`),
  CONSTRAINT `user_center_cart_gen_cart_id_8dcbeada_fk_user_cent` FOREIGN KEY (`cart_id`) REFERENCES `user_center_cart` (`id`),
  CONSTRAINT `user_center_cart_gen_geneinfo_id_677d2edc_fk_user_cent` FOREIGN KEY (`geneinfo_id`) REFERENCES `user_center_geneinfo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=403 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_cart_genes`
--

LOCK TABLES `user_center_cart_genes` WRITE;
/*!40000 ALTER TABLE `user_center_cart_genes` DISABLE KEYS */;
INSERT INTO `user_center_cart_genes` VALUES (7,3,10),(8,3,11),(9,3,12),(10,3,13);
/*!40000 ALTER TABLE `user_center_cart_genes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_geneinfo`
--

DROP TABLE IF EXISTS `user_center_geneinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_geneinfo` (
  `create_date` datetime(6) NOT NULL,
  `id` bigint NOT NULL AUTO_INCREMENT,
  `gene_name` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `original_seq` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `status` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `forbid_seq` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `combined_seq` longtext COLLATE utf8mb4_unicode_ci,
  `saved_seq` longtext COLLATE utf8mb4_unicode_ci,
  `forbidden_check_list` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `contained_forbidden_list` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `gc_content` double DEFAULT NULL,
  `species_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  `vector_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_center_geneinfo_species_id_c0874e68_fk_product_species_id` (`species_id`),
  KEY `user_center_geneinfo_user_id_5cab3c01_fk_auth_user_id` (`user_id`),
  KEY `user_center_geneinfo_vector_id_cfd679cc_fk_product_vector_id` (`vector_id`),
  CONSTRAINT `user_center_geneinfo_species_id_c0874e68_fk_product_species_id` FOREIGN KEY (`species_id`) REFERENCES `product_species` (`id`),
  CONSTRAINT `user_center_geneinfo_user_id_5cab3c01_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `user_center_geneinfo_vector_id_cfd679cc_fk_product_vector_id` FOREIGN KEY (`vector_id`) REFERENCES `product_vector` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_geneinfo`
--

LOCK TABLES `user_center_geneinfo` WRITE;
/*!40000 ALTER TABLE `user_center_geneinfo` DISABLE KEYS */;
INSERT INTO `user_center_geneinfo` VALUES ('2023-11-07 09:19:56.501722',4,'pcbAB-8','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGTGCTTCGTGTTCAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.946353730092206,4,1,18),('2023-11-07 09:19:56.509958',5,'pcbAB-9','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',48.179508890770535,4,1,18),('2023-11-07 09:19:56.520703',6,'pcbAB-10','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','GGGACCGATCCAGCCTCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAATAGAGTCGACAATCAACCTCTGG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.92548687552921,4,1,18),('2023-11-07 10:21:02.296727',7,'pcbAB-11','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.67932489451477,4,1,20),('2023-11-07 10:21:02.306396',8,'pcbAB-12','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.9324894514768,4,1,20),('2023-11-07 10:21:02.314858',9,'pcbAB-13','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCATAG','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.67932489451477,4,1,20),('2023-11-09 11:03:02.992492',10,'pcbAB-10','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.71573604060914,2,4,1),('2023-11-09 11:03:03.003390',11,'pcbAB-11','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTAAACAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATT<em class=\"text-warning\">TGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.71573604060914,2,4,1),('2023-11-09 11:03:03.012428',12,'pcbAB-12','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTGGGGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTA<em class=\"text-warning\">TTTGGGGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.96954314720812,2,4,1),('2023-11-09 11:03:03.020790',13,'pcbAB-13','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.71573604060914,2,4,1),('2023-11-09 11:55:16.791335',14,'pcbAB-14','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.71573604060914,5,1,1),('2023-11-09 11:55:16.802378',15,'pcbAB-15','CCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAACTATTTTTTGGGCCAGCTGGCCCGGAAGCAATCAAAGCCGAAGGAATGGGTCCTCGCTGTCGGTGATAATGAATTTGAATATGGTTTAATGACCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAGCAATTTATTTCTTCCATTGAAGAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGAACCGCCGCGTCAGGGTCCGACCCTCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCCGAAAGTTACTTTAACAACATAGTCAAGAGGCTGAGGCAAACCAACATGGTGGTTTTTAATAACTACTATCTGCATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGCGTCCGAATAATAAATATGAAAGCGAAAATCAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAA','submitted',NULL,'TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGCCGTCTCATCTACTGAAAACATCGTGCAGGGTGTTGTCGCAGTATCTGAACGTTTCAGGCAGGATCCGGCACGTGGAGTCCGTTATGGTACACTTTACGGTTACACACAGCATCCGCTGCCACAGGTTACGGTTAA<em class=\"text-warning\">CTATTTTTTGGGCCAGCTGGCCCGGAAGC</em>AATCAAAGCCGAAGGAATGGGTCCTCGCTGTC<em class=\"text-warning\">GGTGATAATGAATTTGAATATGGTTTAATGA</em>CCAGTCCCGAGGACAAGGATCGTAGTTCATCTGCAGTGGATGTTACCGCTGTTTGCATCGATGGTACCATGATTATTGACGTGGACAGCGCTTGGTCCCTGGAGGAGAGCGAG<em class=\"text-warning\">CAATTTATTTCTTCCATTGAA</em>GAAGGTCTAAACAAGATTCTTGATGGTCGAGCATCTCAACAGACCTCCCGGTTCCCGGATGTTCCACAGCCAGCTGAAACTTACACCCCATATTTCGAATATCTGGA<em class=\"text-warning\">ACCGCCGCGTCAGGGTCCGACCC</em>TCTTCCTGCTGCCCCCAGGCGAAGGTGGTGCC<em class=\"text-warning\">GAAAGTTACTTTAACAACATA</em>GTCAAGAGGCTGAGGCAAACCAACATG<em class=\"text-warning\">GTGGTTTTTAATAACTACTATCTG</em>CATAGCAAACGTTTGCGTACGTTCGAAGAACTGGCCGAAATGTACTTGGACCAAGTGCGTGGTATCCAACCACACGGTCCGTACCATTTCATTGGCTGGTCATTCGGTGGTATTTTGGCTATGGAAATGAGCCGCAGACTTGTCGCAAGCGACGAAAAAATCGGATTTTTGGGCATTATAGACACCTACTTCAACGTTAGAGGTGCTACCAGAACAATAGGGCTCGGGGACACTGAAATCTTAGATCCTATTCACCACATCTACAATCCGGATCCAGCTAACTTTCAACGATTGCCATCCGCTACAGATAGAATCGTCCTGTTTAAAGCAATGC<em class=\"text-warning\">GTCCGAATAATAAATATGAAAGCGAAAAT</em>CAGCGTCGCCTTTACGAATATTACGACGGTACTAGACTTAACGGGCTGGATTCCCTGCTACCAAGCGACTCGGACGTTCAATTAGTTCCGTTGACAGATGATACCCATTTTTCTTGGGTTGGGAATCCCCAGCAAGTTGAACAAATGTGCGCCACCATCAAAGAACATCTAGCACGATACTAAGCTTGGCGTAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',47.71573604060914,5,1,1),('2023-11-16 02:29:16.989367',32,'NB-N-4H7','GCTTCAAACTTCACTCAATTCGTTTTAGTTGATAACGGTGGCGAAGGTAGTCCAGGCTTTCCATTTCGGCCAGATAAGTATAATAAGCGGTTAGTTAATGGTAAGACGCCATGTGAAGGTCGTGTTGAATTGAAAACGTTAGGTGCTTGGGGCTCATTGTGTAATAGTCATTGGGATACTACGGGTGATGTTACTGTTGCTCCATCAAACTTCGCTAACGGTGTTGCTGAATGGATCTCAAGTAACTCACGTAGTCAAGCTTACAAGGTTACTTGTTCAGTTCGTCAATCAAGTGCTCAAAACCGTAAGTACACTATCAAGGTTGAAGTCCCAAAGGTTGCTACTCAAACTGTTGGTGGCGTTGAATTACCAGTTGCTGCGTGGCGTTCATACTTATCAATGGAATTAACTATTCCAATCTTCGCTACTAACTCAGATTGTGAATTAATCGTTAAGGCTATGCAAGGTTTATTGAAGGATGGTAACCCAATCCCATCAGCTATCGCCGCTAACTCAGGTATCTACTTTTATCCGAGTTATCATAGTACGCCGCAACGGCCG','submitted',NULL,'TTGTAAAACGACGGCCAGTGGCTTCAAACTTCACTCAATTCGTTTTAGTTGATAACGGTGGCGAAGGTAGTCCAGGCTTTCCATTTCGGCCAGATAAGTATAATAAGCGGTTAGTTAATGGTAAGACGCCATGTGAAGGTCGTGTTGAATTGAAAACGTTAGGTGCTTGGGGCTCATTGTGTAATAGTCATTGGGATACTACGGGTGATGTTACTGTTGCTCCATCAAACTTCGCTAACGGTGTTGCTGAATGGATCTCAAGTAACTCACGTAGTCAAGCTTACAAGGTTACTTGTTCAGTTCGTCAATCAAGTGCTCAAAACCGTAAGTACACTATCAAGGTTGAAGTCCCAAAGGTTGCTACTCAAACTGTTGGTGGCGTTGAATTACCAGTTGCTGCGTGGCGTTCATACTTATCAATGGAATTAACTATTCCAATCTTCGCTACTAACTCAGATTGTGAATTAATCGTTAAGGCTATGCAAGGTTTATTGAAGGATGGTAACCCAATCCCATCAGCTATCGCCGCTAACTCAGGTATCTACTTTTATCCGAGTTATCATAGTACGCCGCAACGGCCGGCTTGGCGTAATCATGGTCA','TTGTAAAACGACGGCCAGTGGCTTCAAACTTCACTCAATTCGTTTTAGTTGATAACGGTGGCGAAGGTAGTCCAGGCTTTCCATTTCGGCCAGATAA<em class=\"text-warning\">GTATAATAA</em>GCGGTTAGTTAATGGTAAGACGCCATGTGAAGGTCGTGTTGAATTGAAAACGTTAGGTGCTTGGGGCTCATTGTGTAATAGTCATTGGGATACTACGGGTGATGTTACTGTTGCTCCATCAAACTTCGCTAACGGTGTTGCTGAATGGATCTCAAGTAACTCACGTAGTCAAGCTTACAAGGTTACTTGTTCAGTTCGTCAATCAAGTGCTCAAAACCGTAAGTACACTATCAAGGTTGAAGTCCCAAAGGTTGCTACTCAAACTGTTGGTGGCGTTGAATTACCAGTTGCTGCGTGGCGTT<em class=\"text-warning\">CATACTTATCAATGGAATTAACTATT</em>CCAATCTTCGCTACTAACTCAGATTGTGAATTAATCGTTAAGGCTATGCAAGGTTTATTGAAGGATGGTAACCCAATCCCATCAGCTATCGCCGCTAACTCAGGTATCTACTTTTATCCGAGTTATCATAGT<em class=\"text-warning\">ACGCCGCAACGGCCGGCTTGGCG</em>TAATCATGGTCA','[\'GTCTTC\', \'GAAGAC\', \'GAGACC\', \'GGTCTC\']','[]',43.261231281198,NULL,1,1),('2023-11-16 05:52:56.001025',37,'TADAC2.23','MSESEFSHEYWMRHALTLAKRARDERHVPVGAVLVLNNRVIGEGWNRAKGLHDPTAHAEIMALRQGGLVMQNYRLYDATLYSTFEPCVMCAGAMIHSRIGRVVFGVRNAKTGAAGSLMDVLHHPGMNHRVEITEGILADECAELLCRFFRMPRRVFNASKKAQSSTD','submitted',NULL,'MSESEFSHEYWMRHALTLAKRARDERHVPVGAVLVLNNRVIGEGWNRAKGLHDPTAHAEIMALRQGGLVMQNYRLYDATLYSTFEPCVMCAGAMIHSRIGRVVFGVRNAKTGAAGSLMDVLHHPGMNHRVEITEGILADECAELLCRFFRMPRRVFNASKKAQSSTD','MSESEFSHEYWMRHALTLAKRARDERHVPVGAVLVLNNRVIGEGWNRAKGLHDPTAHAEIMALRQGGLVMQNYRLYDATLYSTFEPCVMCAGAMIHSRIGRVVFGVRNAKTGAAGSLMDVLHHPGMNHRVEITEGILADECAELLCRFFRMPRRVFNASKKAQSSTD',NULL,NULL,NULL,2,1,1);
/*!40000 ALTER TABLE `user_center_geneinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_orderinfo`
--

DROP TABLE IF EXISTS `user_center_orderinfo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_orderinfo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `order_time` datetime(6) NOT NULL,
  `status` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `user_id` int NOT NULL,
  PRIMARY KEY (`id`),
  KEY `user_center_orderinfo_user_id_2e26a6f4_fk_auth_user_id` (`user_id`),
  CONSTRAINT `user_center_orderinfo_user_id_2e26a6f4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_orderinfo`
--

LOCK TABLES `user_center_orderinfo` WRITE;
/*!40000 ALTER TABLE `user_center_orderinfo` DISABLE KEYS */;
INSERT INTO `user_center_orderinfo` VALUES (1,'2023-11-07 08:55:31.360713','CREATED',1),(2,'2023-11-07 08:55:48.413439','CREATED',1),(3,'2023-11-07 09:59:59.279861','Pending',1),(4,'2023-11-07 10:08:20.988800','CREATED',1),(5,'2023-11-07 12:23:59.913918','Pending',1),(6,'2023-11-07 12:29:24.302026','CREATED',1),(7,'2023-11-09 12:05:26.080191','CREATED',1),(8,'2023-11-13 05:18:34.409001','CREATED',1),(9,'2023-11-13 05:19:31.689376','CREATED',1),(10,'2023-11-13 05:24:16.344911','CREATED',1),(11,'2023-11-13 05:36:48.199769','CREATED',1),(12,'2023-11-15 02:36:26.405557','CREATED',1),(13,'2023-11-15 10:06:18.879559','CREATED',3),(14,'2023-11-16 02:16:45.317632','CREATED',1),(15,'2023-11-16 02:28:01.091414','CREATED',1),(16,'2023-11-16 03:16:25.045558','CREATED',1),(17,'2023-11-16 03:19:44.263415','CREATED',1),(18,'2023-11-16 03:39:41.936674','CREATED',1),(19,'2023-11-21 02:01:59.504879','CREATED',1);
/*!40000 ALTER TABLE `user_center_orderinfo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_orderinfo_gene_infos`
--

DROP TABLE IF EXISTS `user_center_orderinfo_gene_infos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_orderinfo_gene_infos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `orderinfo_id` bigint NOT NULL,
  `geneinfo_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_center_orderinfo_ge_orderinfo_id_geneinfo_id_de38ce1f_uniq` (`orderinfo_id`,`geneinfo_id`),
  KEY `user_center_orderinf_geneinfo_id_3ebc4445_fk_user_cent` (`geneinfo_id`),
  CONSTRAINT `user_center_orderinf_geneinfo_id_3ebc4445_fk_user_cent` FOREIGN KEY (`geneinfo_id`) REFERENCES `user_center_geneinfo` (`id`),
  CONSTRAINT `user_center_orderinf_orderinfo_id_b43ce964_fk_user_cent` FOREIGN KEY (`orderinfo_id`) REFERENCES `user_center_orderinfo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=61 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_orderinfo_gene_infos`
--

LOCK TABLES `user_center_orderinfo_gene_infos` WRITE;
/*!40000 ALTER TABLE `user_center_orderinfo_gene_infos` DISABLE KEYS */;
INSERT INTO `user_center_orderinfo_gene_infos` VALUES (1,4,4),(2,4,5),(3,6,4),(4,6,5),(5,6,6),(6,6,7),(7,6,8),(8,6,9),(9,7,4),(10,7,5),(11,7,6),(12,7,7),(13,7,8),(14,7,9),(15,7,14),(16,7,15),(17,8,4),(18,8,5),(19,8,6),(20,8,7),(21,8,8),(22,8,9),(23,8,14),(24,8,15),(25,9,4),(26,9,5),(27,9,6),(28,9,7),(29,9,8),(30,9,9),(31,9,14),(32,9,15),(33,10,4),(34,10,5),(35,10,6),(36,10,7),(37,10,8),(38,10,9),(39,10,14),(40,10,15),(57,17,32),(58,18,32),(60,19,37);
/*!40000 ALTER TABLE `user_center_orderinfo_gene_infos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_center_shoppingcart`
--

DROP TABLE IF EXISTS `user_center_shoppingcart`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_center_shoppingcart` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `project_name` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `adding_time` datetime(6) NOT NULL,
  `status` varchar(15) COLLATE utf8mb4_unicode_ci NOT NULL,
  `antibody_number` smallint unsigned DEFAULT NULL,
  `total_price` smallint unsigned NOT NULL,
  `analysis_id` bigint DEFAULT NULL,
  `express_host_id` bigint DEFAULT NULL,
  `product_id` bigint NOT NULL,
  `purification_method_id` bigint NOT NULL,
  `scale_id` bigint DEFAULT NULL,
  `user_id` int NOT NULL,
  `sequence_file` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `user_center_shopping_analysis_id_87f66c1e_fk_product_a` (`analysis_id`),
  KEY `user_center_shopping_product_id_d13d8c1c_fk_product_p` (`product_id`),
  KEY `user_center_shoppingcart_user_id_7ca42ad4_fk_auth_user_id` (`user_id`),
  KEY `user_center_shopping_purification_method__7f77294d_fk_product_p` (`purification_method_id`),
  KEY `user_center_shopping_express_host_id_7b759d54_fk_product_e` (`express_host_id`),
  KEY `user_center_shopping_scale_id_2efc4d72_fk_product_e` (`scale_id`),
  CONSTRAINT `user_center_shopping_analysis_id_87f66c1e_fk_product_a` FOREIGN KEY (`analysis_id`) REFERENCES `product_addon` (`id`),
  CONSTRAINT `user_center_shopping_express_host_id_7b759d54_fk_product_e` FOREIGN KEY (`express_host_id`) REFERENCES `product_expressionhost` (`id`),
  CONSTRAINT `user_center_shopping_product_id_d13d8c1c_fk_product_p` FOREIGN KEY (`product_id`) REFERENCES `product_product` (`id`),
  CONSTRAINT `user_center_shopping_purification_method__7f77294d_fk_product_p` FOREIGN KEY (`purification_method_id`) REFERENCES `product_purificationmethod` (`id`),
  CONSTRAINT `user_center_shopping_scale_id_2efc4d72_fk_product_e` FOREIGN KEY (`scale_id`) REFERENCES `product_expressionscale` (`id`),
  CONSTRAINT `user_center_shoppingcart_user_id_7ca42ad4_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `user_center_shoppingcart_chk_1` CHECK ((`antibody_number` >= 0)),
  CONSTRAINT `user_center_shoppingcart_chk_2` CHECK ((`total_price` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_center_shoppingcart`
--

LOCK TABLES `user_center_shoppingcart` WRITE;
/*!40000 ALTER TABLE `user_center_shoppingcart` DISABLE KEYS */;
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

-- Dump completed on 2023-11-22 17:29:34
