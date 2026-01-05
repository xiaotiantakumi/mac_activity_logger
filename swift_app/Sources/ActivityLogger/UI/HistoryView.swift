import SwiftUI

struct HistoryView: View {
    @State private var selectedDate = Date()
    
    var body: some View {
        VStack {
            HStack {
                DatePicker("Select Date", selection: $selectedDate, displayedComponents: .date)
                    .datePickerStyle(.compact)
                    .labelsHidden()
                Spacer()
            }
            .padding()
            .background(Color(nsColor: .controlBackgroundColor))
            
            List {
                Text("Log entry placeholder 1")
                Text("Log entry placeholder 2")
                Text("Log entry placeholder 3")
            }
            .listStyle(.inset)
        }
    }
}
