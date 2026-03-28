//TIP To <b>Run</b> code, press <shortcut actionId="Run"/> or
// click the <icon src="AllIcons.Actions.Execute"/> icon in the gutter.
void main() {

    Client c1 = new Client();
    c1.setName("Popescu Ion");
    c1.setId(1112);
    c1.setEmail("popescuion@gmail.com");
    c1.setAddress("St. Primaverii, Nr. 23");
    c1.setPhone("0783452311");

    Products p = new Products("Masa stejar", 1200.99);

    c1.addProduct(p);
    c1.placeOrder();

}
