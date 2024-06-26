-- phpMyAdmin SQL Dump
-- version 4.9.2
-- https://www.phpmyadmin.net/
--
-- Hôte : 127.0.0.1:3306
-- Généré le :  lun. 10 juin 2024 à 12:08
-- Version du serveur :  10.4.10-MariaDB
-- Version de PHP :  7.4.0

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET AUTOCOMMIT = 0;
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données :  `dl_sion_compagnie`
--

-- --------------------------------------------------------

--
-- Structure de la table `administrateur`
--

DROP TABLE IF EXISTS `administrateur`;
CREATE TABLE IF NOT EXISTS `administrateur` (
  `id_admin` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(250) NOT NULL,
  `prenom` varchar(250) NOT NULL,
  `telephone` varchar(14) NOT NULL,
  `email` varchar(250) NOT NULL,
  `login` varchar(250) NOT NULL,
  `mot_pass` varchar(250) NOT NULL,
  `image` blob DEFAULT NULL,
  PRIMARY KEY (`id_admin`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `administrateur`
--

INSERT INTO `administrateur` (`id_admin`, `nom`, `prenom`, `telephone`, `email`, `login`, `mot_pass`, `image`) VALUES
(17, 'Benoit Kra', 'Adelphe', '75934211', 'adelphekra@gmail.com', 'soum1234', '$2b$12$m7amhXMWkkFT/lLVWbf4LeMPqRpGHrxOr125KVklRznAWwXxLEHEe', 0x53637265656e73686f745f323032312d30372d32342d31392d31372d31312e706e67);

-- --------------------------------------------------------

--
-- Structure de la table `client`
--

DROP TABLE IF EXISTS `client`;
CREATE TABLE IF NOT EXISTS `client` (
  `id_client` int(11) NOT NULL AUTO_INCREMENT,
  `nom_prenoms` varchar(250) NOT NULL,
  `telephone` varchar(14) NOT NULL,
  `email` varchar(250) NOT NULL,
  `adresse` varchar(250) NOT NULL,
  `statut` varchar(250) NOT NULL,
  PRIMARY KEY (`id_client`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `client`
--
-- --------------------------------------------------------

--
-- Structure de la table `commande`
--

DROP TABLE IF EXISTS `commande`;
CREATE TABLE IF NOT EXISTS `commande` (
  `id_commande` int(11) NOT NULL AUTO_INCREMENT,
  `id_client` int(11) NOT NULL,
  `id_produit` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `prix_vente` int(11) NOT NULL,
  `Montant` int(11) NOT NULL,
  `date_commande` datetime NOT NULL,
  `statut` varchar(255) NOT NULL,
  `id_utilisateur` int(11) DEFAULT NULL,
  `id_admin` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_commande`),
  KEY `fk_commande_id_utilisateur` (`id_utilisateur`),
  KEY `fk_id_client` (`id_client`),
  KEY `fk_commande_id_produit` (`id_produit`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `commande`
--

-- --------------------------------------------------------

--
-- Structure de la table `entree`
--

DROP TABLE IF EXISTS `entree`;
CREATE TABLE IF NOT EXISTS `entree` (
  `id_entree` int(11) NOT NULL AUTO_INCREMENT,
  `id_fournisseur` int(11) NOT NULL,
  `id_produit` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `prix` int(11) NOT NULL,
  `date_entree` datetime NOT NULL,
  `statut` varchar(255) NOT NULL,
  PRIMARY KEY (`id_entree`),
  KEY `fk_entree_id_produit` (`id_produit`),
  KEY `fk_entree_id_fournisseur` (`id_fournisseur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `entree`
--

-- --------------------------------------------------------

--
-- Structure de la table `facture`
--

DROP TABLE IF EXISTS `facture`;
CREATE TABLE IF NOT EXISTS `facture` (
  `id_facture` int(11) NOT NULL AUTO_INCREMENT,
  `id_client` int(11) NOT NULL,
  `id_ventes` int(11) NOT NULL,
  `id_produit` int(11) NOT NULL,
  `numero_F` varchar(255) NOT NULL,
  `reçu` longblob NOT NULL,
  PRIMARY KEY (`id_facture`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Structure de la table `fournisseur`
--

DROP TABLE IF EXISTS `fournisseur`;
CREATE TABLE IF NOT EXISTS `fournisseur` (
  `id_fournisseur` int(11) NOT NULL AUTO_INCREMENT,
  `nom_prenoms` varchar(250) NOT NULL,
  `telephone` varchar(14) NOT NULL,
  `email` varchar(250) NOT NULL,
  `adresse` varchar(250) NOT NULL,
  PRIMARY KEY (`id_fournisseur`)
) ENGINE=InnoDB  DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `fournisseur`
--
-- --------------------------------------------------------

--
-- Structure de la table `produit`
--

DROP TABLE IF EXISTS `produit`;
CREATE TABLE IF NOT EXISTS `produit` (
  `id_produit` int(11) NOT NULL AUTO_INCREMENT,
  `nom_produit` varchar(250) NOT NULL,
  `categorie` varchar(250) NOT NULL,
  `prix` int(11) NOT NULL,
  `stock` int(11) NOT NULL,
  `stock_min` int(11) DEFAULT NULL,
  `designation` text NOT NULL,
  `image` blob DEFAULT NULL,
  PRIMARY KEY (`id_produit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `produit`
--


-- --------------------------------------------------------

--
-- Structure de la table `stock`
--

DROP TABLE IF EXISTS `stock`;
CREATE TABLE IF NOT EXISTS `stock` (
  `id_stock` int(11) NOT NULL AUTO_INCREMENT,
  `id_produit` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `date` datetime NOT NULL,
  `id_utilisateur` int(11) DEFAULT NULL,
  PRIMARY KEY (`id_stock`),
  KEY `fk_stock_id_utilisateur` (`id_utilisateur`),
  KEY `fk_stock_idproduit` (`id_produit`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `stock`
--


-- --------------------------------------------------------

--
-- Structure de la table `utilisateur`
--

DROP TABLE IF EXISTS `utilisateur`;
CREATE TABLE IF NOT EXISTS `utilisateur` (
  `id_utilisateur` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(250) NOT NULL,
  `prenom` varchar(250) NOT NULL,
  `poste` varchar(255) DEFAULT NULL,
  `telephone` varchar(14) NOT NULL,
  `email` varchar(250) NOT NULL,
  `login` varchar(250) NOT NULL,
  `mot_pass` varchar(250) NOT NULL,
  `image` blob DEFAULT NULL,
  `mot_pass_clair` varchar(250) NOT NULL,
  PRIMARY KEY (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `utilisateur`
--

-- --------------------------------------------------------

--
-- Structure de la table `vente`
--

DROP TABLE IF EXISTS `vente`;
CREATE TABLE IF NOT EXISTS `vente` (
  `id_vente` int(11) NOT NULL AUTO_INCREMENT,
  `id_produit` int(11) NOT NULL,
  `id_client` int(11) NOT NULL,
  `quantite` int(11) NOT NULL,
  `montant` int(11) NOT NULL,
  `prix_vente` int(11) NOT NULL,
  `date_vente` datetime NOT NULL,
  `statut` varchar(250) NOT NULL,
  `id_utilisateur` int(11) DEFAULT NULL,
  `id_admin` int(11) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id_vente`),
  KEY `fk_id_utilisateur` (`id_utilisateur`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Déchargement des données de la table `vente`
--

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `commande`
--
ALTER TABLE `commande`
  ADD CONSTRAINT `fk_commande_id_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_commande_id_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_id_client` FOREIGN KEY (`id_client`) REFERENCES `client` (`id_client`) ON DELETE CASCADE;

--
-- Contraintes pour la table `entree`
--
ALTER TABLE `entree`
  ADD CONSTRAINT `fk_entree_id_fournisseur` FOREIGN KEY (`id_fournisseur`) REFERENCES `fournisseur` (`id_fournisseur`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_entree_id_produit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`) ON DELETE CASCADE;

--
-- Contraintes pour la table `stock`
--
ALTER TABLE `stock`
  ADD CONSTRAINT `fk_stock_id_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_stock_idproduit` FOREIGN KEY (`id_produit`) REFERENCES `produit` (`id_produit`) ON DELETE CASCADE;

--
-- Contraintes pour la table `vente`
--
ALTER TABLE `vente`
  ADD CONSTRAINT `fk_id_utilisateur` FOREIGN KEY (`id_utilisateur`) REFERENCES `utilisateur` (`id_utilisateur`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
