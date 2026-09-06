import java.sql.*;
import java.util.*;
import java.io.*;
import org.json.JSONArray;
import org.json.JSONObject;

class Lorry {
    String plateNumber;
    double grossWeight;
    double tareWeight;
    double netWeight;
    double revenue;
    double fine;
    String date;
    String type;

    public Lorry(String plateNumber, double grossWeight, double tareWeight, String type, double ratePerTon, String date) {
        this.plateNumber = plateNumber;
        this.grossWeight = grossWeight;
        this.tareWeight = tareWeight;
        this.netWeight = grossWeight - tareWeight;
        this.type = type;
        this.revenue = this.netWeight * ratePerTon;
        this.fine = calculateFine();
        this.date = date;
    }

    private double calculateFine() {
        double excess = 0, fineAmount = 0;
        switch(type.toLowerCase()) {
            case "lcv": excess = Math.max(0, netWeight - 3); fineAmount = excess * 5000; break;
            case "medium": excess = Math.max(0, netWeight - 10); fineAmount = excess * 7000; break;
            case "heavy": excess = Math.max(0, netWeight - 20); fineAmount = excess * 10000; break;
            case "tanker": excess = Math.max(0, netWeight - 25); fineAmount = excess * 15000; break;
            default: fineAmount = 0;
        }
        return fineAmount;
    }

    public JSONObject toJSON() {
        JSONObject obj = new JSONObject();
        obj.put("plate", plateNumber);
        obj.put("type", type);
        obj.put("gross", grossWeight);
        obj.put("tare", tareWeight);
        obj.put("net", netWeight);
        obj.put("revenue", revenue);
        obj.put("fine", fine);
        obj.put("date", date);
        return obj;
    }
}

public class EagleRevenueSystemJSON {
    static final String DB_URL = "jdbc:sqlite:eagle.db";
    static final double RATE_PER_TON = 50.0;

    public static void main(String[] args) {
        EagleRevenueSystemJSON system = new EagleRevenueSystemJSON();
        system.createTableIfNotExists();
        Scanner scanner = new Scanner(System.in);
        int choice;
        do {
            displayMenu();
            choice = scanner.nextInt();
            scanner.nextLine();
            switch(choice) {
                case 1 -> system.addLorryRecord(scanner);
                case 2 -> system.displayAllLorriesJSON();
                case 3 -> system.dailySummaryJSON();
                case 4 -> system.monthlySummaryJSON();
                case 0 -> System.out.println("Exiting...");
                default -> System.out.println("Invalid option!");
            }
        } while(choice != 0);
        scanner.close();
    }

    static void displayMenu() {
        System.out.println("\n=== EAGLE Revenue System JSON ===");
        System.out.println("1. Add Lorry Record");
        System.out.println("2. Display All Lorries (JSON)");
        System.out.println("3. Daily Summary (JSON)");
        System.out.println("4. Monthly Summary (JSON)");
        System.out.println("0. Exit");
        System.out.print("Enter choice: ");
    }

    void createTableIfNotExists() {
        try(Connection conn = DriverManager.getConnection(DB_URL);
            Statement stmt = conn.createStatement()) {
            String sql = """
                CREATE TABLE IF NOT EXISTS lorries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plate TEXT NOT NULL,
                    type TEXT NOT NULL,
                    gross REAL NOT NULL,
                    tare REAL NOT NULL,
                    net REAL NOT NULL,
                    revenue REAL NOT NULL,
                    fine REAL NOT NULL,
                    date TEXT NOT NULL
                );
            """;
            stmt.execute(sql);
        } catch(SQLException e) {
            System.out.println("Error creating table: " + e.getMessage());
        }
    }

    void addLorryRecord(Scanner scanner) {
        try(Connection conn = DriverManager.getConnection(DB_URL);
            PreparedStatement pstmt = conn.prepareStatement(
                "INSERT INTO lorries(plate, type, gross, tare, net, revenue, fine, date) VALUES(?,?,?,?,?,?,?,?)")) {

            System.out.print("Enter plate number: ");
            String plate = scanner.nextLine();
            System.out.print("Enter vehicle type (LCV/Medium/Heavy/Tanker): ");
            String type = scanner.nextLine();
            System.out.print("Enter gross weight: ");
            double gross = scanner.nextDouble();
            System.out.print("Enter tare weight: ");
            double tare = scanner.nextDouble();
            scanner.nextLine();
            System.out.print("Enter date (yyyy-MM-dd): ");
            String date = scanner.nextLine();

            Lorry lorry = new Lorry(plate, gross, tare, type, RATE_PER_TON, date);

            pstmt.setString(1, lorry.plateNumber);
            pstmt.setString(2, lorry.type);
            pstmt.setDouble(3, lorry.grossWeight);
            pstmt.setDouble(4, lorry.tareWeight);
            pstmt.setDouble(5, lorry.netWeight);
            pstmt.setDouble(6, lorry.revenue);
            pstmt.setDouble(7, lorry.fine);
            pstmt.setString(8, lorry.date);

            pstmt.executeUpdate();
            System.out.println("Record added successfully: " + lorry.toJSON().toString());

        } catch(SQLException e) {
            System.out.println("Error adding record: " + e.getMessage());
        }
    }

    void displayAllLorriesJSON() {
        try(Connection conn = DriverManager.getConnection(DB_URL);
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery("SELECT * FROM lorries")) {

            JSONArray jsonArray = new JSONArray();
            while(rs.next()) {
                Lorry lorry = new Lorry(
                    rs.getString("plate"),
                    rs.getDouble("gross"),
                    rs.getDouble("tare"),
                    rs.getString("type"),
                    RATE_PER_TON,
                    rs.getString("date")
                );
                jsonArray.put(lorry.toJSON());
            }
            System.out.println(jsonArray.toString(4)); // pretty print

        } catch(SQLException e) {
            System.out.println("Error fetching lorries: " + e.getMessage());
        }
    }

    void dailySummaryJSON() {
        try(Connection conn = DriverManager.getConnection(DB_URL);
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(
                "SELECT date, SUM(revenue) AS totalRevenue, SUM(fine) AS totalFines FROM lorries GROUP BY date")) {

            JSONArray dailyArray = new JSONArray();
            while(rs.next()) {
                JSONObject obj = new JSONObject();
                obj.put("date", rs.getString("date"));
                obj.put("totalRevenue", rs.getDouble("totalRevenue"));
                obj.put("totalFines", rs.getDouble("totalFines"));
                dailyArray.put(obj);
            }
            System.out.println(dailyArray.toString(4));

        } catch(SQLException e) {
            System.out.println("Error generating daily summary: " + e.getMessage());
        }
    }

    void monthlySummaryJSON() {
        try(Connection conn = DriverManager.getConnection(DB_URL);
            Statement stmt = conn.createStatement();
            ResultSet rs = stmt.executeQuery(
                "SELECT SUBSTR(date,1,7) AS month, SUM(revenue) AS totalRevenue, SUM(fine) AS totalFines FROM lorries GROUP BY month")) {

            JSONArray monthlyArray = new JSONArray();
            while(rs.next()) {
                JSONObject obj = new JSONObject();
                obj.put("month", rs.getString("month"));
                obj.put("totalRevenue", rs.getDouble("totalRevenue"));
                obj.put("totalFines", rs.getDouble("totalFines"));
                monthlyArray.put(obj);
            }
            System.out.println(monthlyArray.toString(4));

        } catch(SQLException e) {
            System.out.println("Error generating monthly summary: " + e.getMessage());
        }
    }
}
