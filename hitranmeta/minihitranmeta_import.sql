INSERT INTO minihitran.hitranmeta_molecule (
    molecID, molecID_str, InChI, InChIKey, stoichiometric_formula,
    ordinary_formula, ordinary_formula_html, common_name, cml)
SELECT m.speciesID_i, m.speciesID, s.InChI, s.InChIKey,
       s.stoichiometric_formula, s.ordinary_formula, s.ordinary_formula_html,
       s.common_name, s.cml
FROM VAMDC_species.species_species_db m, VAMDC_species.species_species s
    WHERE m.species_id=s.id AND m.name="HITRAN";

INSERT INTO minihitran.hitranmeta_iso (
    isoID, isoID_str, InChI_explicit, InChIKey_explicit, InChI, InChIKey,
    molecule_id, iso_name, iso_name_html, abundance, afgl_code,
    cml_explicit, cml)
SELECT m.isoID_i, m.isoID, i.InChI_explicit, i.InChIKey_explicit, i.InChI,
       i.InChIKey, m.speciesID_i, i.iso_name, i.iso_name_html, i.abundance,
       i.afgl_code, i.cml_explicit, i.cml
FROM VAMDC_species.species_iso_db m, VAMDC_species.species_iso i
    WHERE m.iso_id=i.id AND m.name="HITRAN";

INSERT INTO minihitran.hitranmeta_moleculename (
    name, molecule_id)
SELECT n.name, m.speciesID_i
FROM VAMDC_species.species_species_db m, VAMDC_species.species_speciesname n
    WHERE m.species_id=n.species_id AND m.name="HITRAN";
       
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (0, 'gen', "General case");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (1, 'dcs', "Closed-shell diatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (2, 'hunda', "Hund's case (a) diatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (3, 'hundb', "Hund's case (b) diatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (4, 'ltcs', "Closed-shell linear triatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (5, 'nltcs', "Closed-shell non-linear triatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (6, 'stcs', "Closed-shell symmetric top");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (7, 'lpcs', "Closed-shell linear polyatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (8, 'asymcs', "Closed-shell asymmetric top");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (9, 'asymos', "Open-shell asymmetric top");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (10, 'sphcs', "Closed-shell spherical top");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (11, 'sphos', "Open-shell spherical top");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (12, 'ltos', "Open-shell linear triatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (13, 'lpos', "Open-shell linear polyatomic");
INSERT INTO minihitran.hitranmeta_case (id, case_prefix, case_description)
VALUES (14, 'nltos', "Open-shell non-linear triatomic");
