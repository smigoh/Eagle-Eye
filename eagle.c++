#include <iostream>
#include <vector>
#include <string>
#include <ctime>
#include <sqlite3.h>
using namespace std;

// -----------------------------
// Structures
// -----------------------------
struct Lorry {
    int id;
    string plate_number;
    double gross_weight;
    double tare_weight;
    double net_weight;
    time_t weigh_time;
};

struct Revenue {
    int id;
    int lorry_id;
    double amount;
    time_t recorded_time;
};

// -----------------------------
// Database Helper
// -----------------------------
class Database {
private:
    sqlite3* db;
public:
    Database(const string& db_file) {
        if (sqlite3_open(db_file.c_str(), &db)) {
            cerr << "Can't open database: " << sqlite3_errmsg(db) << endl;
            exit(1);
        }
    }

    ~Database() {
        sqlite3_close(db);
    }

    // Execute query without return
    void execute(const string& sql) {
        char* errMsg = nullptr;
        if (sqlite3_exec(db, sql.c_str(), 0, 0, &errMsg) != SQLITE_OK) {
            cerr << "SQL error: " << errMsg << endl;
            sqlite3_free(errMsg);
        }
    }

    // Insert Lorry
    void insertLorry(const Lorry& lorry) {
        string sql = "INSERT INTO lorries (plate_number, gross_weight, tare_weight, net_weight, weigh_time) VALUES ('" +
                     lorry.plate_number + "', " +
                     to_string(lorry.gross_weight) + ", " +
                     to_string(lorry.tare_weight) + ", " +
                     to_string(lorry.net_weight) + ", " +
                     to_string(lorry.weigh_time) + ");";
        execute(sql);
    }

    // Insert Revenue
    void insertRevenue(const Revenue& rev) {
        string sql = "INSERT INTO revenue (lorry_id, amount, recorded_time) VALUES (" +
                     to_string(rev.lorry_id) + ", " +
                     to_string(rev.amount) + ", " +
                     to_string(rev.recorded_time) + ");";
        execute(sql);
    }

    // Fetch all lorries
    vector<Lorry> getLorries() {
        vector<Lorry> lorries;
        sqlite3_stmt* stmt;
        string sql = "SELECT * FROM lorries;";
        if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, 0) != SQLITE_OK) {
            cerr << "Failed to fetch lorries." << endl;
            return lorries;
        }
        while (sqlite3_step(stmt) == SQLITE_ROW) {
            Lorry l;
            l.id = sqlite3_column_int(stmt, 0);
            l.plate_number = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 1));
            l.gross_weight = sqlite3_column_double(stmt, 2);
            l.tare_weight = sqlite3_column_double(stmt, 3);
            l.net_weight = sqlite3_column_double(stmt, 4);
            l.weigh_time = sqlite3_column_int(stmt, 5);
            lorries.push_back(l);
        }
        sqlite3_finalize(stmt);
        return lorries;
    }

    // Fetch revenue for a lorry
    double getRevenueByLorry(int lorry_id) {
        double total = 0;
        sqlite3_stmt* stmt;
        string sql = "SELECT SUM(amount) FROM revenue WHERE lorry_id=" + to_string(lorry_id) + ";";
        if (sqlite3_prepare_v2(db, sql.c_str(), -1, &stmt, 0) != SQLITE_OK) return total;
        if (sqlite3_step(stmt) == SQLITE_ROW) {
            total = sqlite3_column_double(stmt, 0);
        }
        sqlite3_finalize(stmt);
        return total;
    }
};

// -----------------------------
// Eagle Algorithms (Math & Data Structures)
// -----------------------------
double calculateNetWeight(double gross, double tare) {
    return gross - tare;
}

double calculateRevenue(double net_weight, double rate_per_ton) {
    return net_weight * rate_per_ton;
}

// Sorting lorries by net weight (descending)
void sortLorriesByNetWeight(vector<Lorry>& lorries) {
    for (size_t i = 0; i < lorries.size(); i++) {
        for (size_t j = i + 1; j < lorries.size(); j++) {
            if (lorries[j].net_weight > lorries[i].net_weight) {
                swap(lorries[i], lorries[j]);
            }
        }
    }
}

// -----------------------------
// UI & Interaction
// -----------------------------
void displayLorries(const vector<Lorry>& lorries) {
    cout << "\n--- Lorries ---\n";
    for (const auto& l : lorries) {
        cout << "ID: " << l.id
             << " | Plate: " << l.plate_number
             << " | Gross: " << l.gross_weight
             << " | Tare: " << l.tare_weight
             << " | Net: " << l.net_weight
             << " | Time: " << ctime(&l.weigh_time);
    }
}

int main() {
    Database db("eagle.db");

    // Ensure tables exist
    db.execute("CREATE TABLE IF NOT EXISTS lorries (id INTEGER PRIMARY KEY AUTOINCREMENT, plate_number TEXT, gross_weight REAL, tare_weight REAL, net_weight REAL, weigh_time INTEGER);");
    db.execute("CREATE TABLE IF NOT EXISTS revenue (id INTEGER PRIMARY KEY AUTOINCREMENT, lorry_id INTEGER, amount REAL, recorded_time INTEGER, FOREIGN KEY(lorry_id) REFERENCES lorries(id));");

    int choice;
    vector<Lorry> lorries;

    while (true) {
        cout << "\nEagle System Menu:\n";
        cout << "1. Add Lorry\n2. Calculate Revenue\n3. Display Lorries\n4. Exit\nChoice: ";
        cin >> choice;

        if (choice == 1) {
            Lorry l;
            cout << "Plate Number: "; cin >> l.plate_number;
            cout << "Gross Weight: "; cin >> l.gross_weight;
            cout << "Tare Weight: "; cin >> l.tare_weight;
            l.net_weight = calculateNetWeight(l.gross_weight, l.tare_weight);
            l.weigh_time = time(0);

            db.insertLorry(l);
            cout << "Lorry added successfully!\n";

        } else if (choice == 2) {
            lorries = db.getLorries();
            sortLorriesByNetWeight(lorries);

            for (const auto& l : lorries) {
                double rev = calculateRevenue(l.net_weight, 50); // rate_per_ton = 50
                Revenue r{0, l.id, rev, time(0)};
                db.insertRevenue(r);
                cout << "Revenue for Lorry " << l.plate_number << ": " << rev << endl;
            }

        } else if (choice == 3) {
            lorries = db.getLorries();
            sortLorriesByNetWeight(lorries);
            displayLorries(lorries);

        } else if (choice == 4) {
            cout << "Exiting system...\n";
            break;
        } else {
            cout << "Invalid choice!\n";
        }
    }

    return 0;
}
