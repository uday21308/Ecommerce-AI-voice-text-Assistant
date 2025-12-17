export default function ToolPanel({ toolInfo, retrievedDocs }) {
  return (
    <div>
      <h2 className="font-semibold mb-3">Tool Activity</h2>

      {/* Tool info */}
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-1">Last Tool Used</h3>
        {toolInfo ? (
          <pre className="bg-gray-100 rounded p-2 text-xs overflow-auto">
            {JSON.stringify(toolInfo, null, 2)}
          </pre>
        ) : (
          <p className="text-sm text-gray-500">No tool used yet</p>
        )}
      </div>

      {/* Retrieved docs */}
      <div>
        <h3 className="text-sm font-medium mb-1">Retrieved Context</h3>
        {retrievedDocs && retrievedDocs.length > 0 ? (
          <ul className="space-y-2">
            {retrievedDocs.map((doc, idx) => (
              <li key={idx} className="bg-gray-100 p-2 rounded text-xs">
                <p className="font-semibold">{doc.title || doc.source}</p>
                {doc.final_price && (
                  <p>Price: {doc.final_price}</p>
                )}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-gray-500">No documents retrieved</p>
        )}
      </div>
    </div>
  )
}
