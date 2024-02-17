CREATE TABLE sous_categ(
   id_sous_categ INT,
   nom_sous_categ VARCHAR(80),
   id_categ INT,
   PRIMARY KEY(id_sous_categ),
   FOREIGN KEY(id_categ) REFERENCES categ(id_categ)
);


INSERT INTO sous_categ 
	values 
(1,'Fruit et Legume',5),
(2,'Electromenager',2),
(3,'Habillement',4),
(4,'Sante',7),
(5,'Dechet',1),
(6,'Viande',5),
(7,'Pain',5),
(8,'Boisson',5),
(9,'Traiteur',6),
(10,'Accompagnement Social',3),
(11,'Epices',5),
(12,'Restaurant',6),
(13,'Reparation Velo',9),
(14,'Culture',3),
(15,'Don Alimentaire',8),
(16,'Don non Aimentaire',8),
(17,'Sucre',5),
(18,'Hygiene',7),
(19,'Fromage',5),
(20,'Poisson',5),
(21,'Bricolage',9),
(22,'Jardinage',3),
(23,'Meubles',2),
(24,'Cours',3),
(25,'Autoreparation Objet',9),
(26,'Pressing',4),
(27,'Recharge de cartouche',2);