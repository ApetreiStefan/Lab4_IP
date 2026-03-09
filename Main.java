public class Main {

    public static void main(String[] args) {
        AutentificareSiAccesManager manager = new AutentificareSiAccesManager();

        AutentificareSiAccesManager.StatusAutentificare statusEroare = manager.login("client@emag.ro", "1234");
        System.out.println("Rezultat logare 1: " + statusEroare);

        AutentificareSiAccesManager.StatusAutentificare statusSucces = manager.login("client@emag.ro", "parola123");
        System.out.println("Rezultat logare 2: " + statusSucces);

        if (statusSucces == AutentificareSiAccesManager.StatusAutentificare.SUCCES) {
            System.out.println("\nIntram in aplicatie");

            AutentificareSiAccesManager.CatalogResponse raspunsCatalog = manager.vizualizareCatalog();
            System.out.println(raspunsCatalog.mesajSistem);

            for (AutentificareSiAccesManager.Produs produs : raspunsCatalog.produseRecomandate) {
                System.out.println("Produs: " + produs.nume + " | Pret: " + produs.pret + " RON");
            }

            System.out.println("\nUtilizatorul cauta un produs");
            var rezultateCautare = manager.cautareProdus("Casti Wireless");
            for (AutentificareSiAccesManager.Produs rezultat : rezultateCautare) {
                System.out.println("Gasit: " + rezultat.nume + " | Pret: " + rezultat.pret + " RON");
            }
        }
    }
}