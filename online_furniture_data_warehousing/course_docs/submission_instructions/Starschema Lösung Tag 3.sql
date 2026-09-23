create database ....

use database ...


create schema dwh1
go


----- dimensionen dwh1.D_Kunden
----- FAKT dwh1.F_Einkaeufe

drop table if exists dwh1.Kunden
create table dwh1.Kunden
(
	Kunde bigint PRIMARY KEY IDENTITY(1,1) NOT NULL,
	WOhnOrtdesKunden varchar(100) NOT NULL,
	LandkreiusdesKunden varchar(100) NOT NULL
)

CREATE TABLE [dwh1].[Artikel](
	[Artikel] [bigint] PRIMARY KEY IDENTITY(1,1) NOT NULL,
	[Artikelgruppe] [varchar](5) NOT NULL,
	[ArtikelObergruppe] [varchar](5) NOT NULL,
)

create table dwh1.Kassa
(
	Kassa bigint PRIMARY KEY IDENTITY(1,1) NOT NULL,
	Filiale varchar(100) NOT NULL,
	Filialbezirk varchar(100) NOT NULL,
	Filialoberbezirk varchar(100) NOT NULL ,
	FilialLandkreis varchar(100) NOT NULL,
	FilialBundesland varchar(100) NOT NULL,
	FilialStaat varchar(100) NOT NULL
)

create table dwh1.Zeit  --- dwh1.D_Zeit
(
	Tag char(8) PRIMARY KEY NOT NULL ,--JJJJMMTT
	Woche varchar(6) NOT NULL, --- JJJJWW
	Monat varchar(6) NOT NULL, --JJJJMM
	Jahr varchar(4) NOT NULL ---JJJJ
)

create table dwh1.F_Einkaeufe
(
	Kunde bigint NOT NULL,
	[Artikel] [bigint] NOT NULL,
	Kassa bigint NOT NULL,
	Tag char(8) NOT NULL,
	Menge integer NOT NULL default(1) check(Menge > 0),
	Verkaufspreis decimal(8,2) default(10),
	FOREIGN KEY (Kunde) REFERENCES dwh1.Kunden(Kunde),
	FOREIGN KEY (Artikel) REFERENCES dwh1.Artikel(Artikel),
	FOREIGN KEY (Kassa) REFERENCES dwh1.Kassa(Kassa),
	FOREIGN KEY (Tag) REFERENCES dwh1.Zeit(Tag),
	PRIMARY KEY (Kunde, Artikel, Kassa, Tag)
	--PRIMARY KEY (Tag, Kunde, Artikel, Kassa, )
)