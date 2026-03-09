import java.util.ArrayList;
import java.util.List;

public class AutentificareSiAccesManager {

    public enum StatusAutentificare {
        SUCCES,
        EMAIL_INEXISTENT,
        PAROLA_INCORECTA,
        CONT_BLOCAT
    }

    public class Produs {
        public String id;
        public String nume;
        public double pret;

        public Produs(String id, String nume, double pret) {
            this.id = id;
            this.nume = nume;
            this.pret = pret;
        }
    }

    public class CatalogResponse {
        public List<Produs> produseRecomandate;
        public String mesajSistem;
    }

    public StatusAutentificare login(String email, String parola) {
        if (!email.equals("client@emag.ro")) {
            return StatusAutentificare.EMAIL_INEXISTENT;
        }
        if (!parola.equals("parola123")) {
            return StatusAutentificare.PAROLA_INCORECTA;
        }
        return StatusAutentificare.SUCCES;
    }

    public List<Produs> vizualizareRecentePopulare() {
        List<Produs> lista = new ArrayList<>();
        lista.add(new Produs("P1", "Telefon Smart", 4500.00));
        lista.add(new Produs("P2", "Laptop Gaming", 8000.50));
        return lista;
    }

    public Produs vizualizareDetaliiProdus(String idProdus) {
        return new Produs(idProdus, "Produs Detaliat", 150.00);
    }

    public List<Produs> cautareProdus(String keyword) {
        List<Produs> rezultate = new ArrayList<>();
        rezultate.add(new Produs("P3", "Rezultat pentru: " + keyword, 100.00));
        return rezultate;
    }

    public CatalogResponse vizualizareCatalog() {
        CatalogResponse response = new CatalogResponse();

        response.produseRecomandate = vizualizareRecentePopulare();
        response.mesajSistem = "Catalog incarcat cu succes. Folositi metodele de cautare pentru mai multe.";

        return response;
    }
}