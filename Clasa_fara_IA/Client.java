import java.util.ArrayList;
import java.util.List;

public class Client {

    private String name;
    private int id;
    private String email;
    private String address;
    private String phone;

    private final List<Products> shoppingCart;
    private final List<Products> boughtProducts;

    public Client() {
        shoppingCart = new ArrayList<>();
        boughtProducts = new ArrayList<>();
    }

    public void addProduct(Products p)
    {
        if(p != null)
        {
            shoppingCart.add(p);
            System.out.println("The product was added in shopping cart!");
        }
        else
        {
            System.out.println("The product is not in stock");
        }
    }

    public void placeOrder()
    {
        if(!shoppingCart.isEmpty())
        {
            boughtProducts.addAll(shoppingCart);
            shoppingCart.clear();

            System.out.println("Placed Order!");
        }
        else
        {
            System.out.println("Shopping cart is empty!");
        }
    }

    public List<Products> getBoughtProducts()
    {
        return boughtProducts;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public int getId() {
        return id;
    }

    public void setId(int id) {
        this.id = id;
    }


    public String getEmail() {
        return email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getAddress() {
        return address;
    }

    public void setAddress(String address) {
        this.address = address;
    }

    public String getPhone() {
        return phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }
}