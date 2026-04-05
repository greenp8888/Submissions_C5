import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Files, FolderOpen, UploadCloud } from "lucide-react";

import { fetchCollectionDetails, fetchCollections, uploadKnowledge } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function KnowledgeManager() {
  const queryClient = useQueryClient();
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>("");
  const [collectionName, setCollectionName] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const collectionsQuery = useQuery({
    queryKey: ["collections"],
    queryFn: fetchCollections,
  });

  const detailsQuery = useQuery({
    queryKey: ["collection-details", selectedCollectionId],
    queryFn: () => fetchCollectionDetails(selectedCollectionId),
    enabled: Boolean(selectedCollectionId),
  });

  const uploadMutation = useMutation({
    mutationFn: () => uploadKnowledge(collectionName, files),
    onSuccess: async (result) => {
      setMessage(`Indexed ${result.document_ids.length} document(s) into ${collectionName}.`);
      setCollectionName("");
      setFiles([]);
      setSelectedCollectionId(result.collection_id);
      await queryClient.invalidateQueries({ queryKey: ["collections"] });
      await queryClient.invalidateQueries({ queryKey: ["collection-details", result.collection_id] });
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Failed to upload knowledge files.");
    },
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader>
          <CardTitle>Upload and index research documents</CardTitle>
          <CardDescription>Create a collection from PDFs, markdown, or plain text files for local-first RAG retrieval and online knowledge building.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="space-y-2">
            <Label htmlFor="collection-name">Collection name</Label>
            <Input
              id="collection-name"
              placeholder="Battery landscape corpus"
              value={collectionName}
              onChange={(event) => setCollectionName(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="knowledge-files">Files</Label>
            <Input
              id="knowledge-files"
              type="file"
              multiple
              accept=".pdf,.txt,.md"
              onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
            />
            {files.length ? (
              <div className="rounded-xl bg-muted/70 p-3 text-sm text-muted-foreground">
                {files.map((file) => file.name).join(", ")}
              </div>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button
              onClick={() => uploadMutation.mutate()}
              disabled={!collectionName.trim() || files.length === 0 || uploadMutation.isPending}
            >
              <UploadCloud className="h-4 w-4" />
              {uploadMutation.isPending ? "Uploading…" : "Upload collection"}
            </Button>
            {message ? <p className="text-sm text-muted-foreground">{message}</p> : null}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Research document collections</CardTitle>
          <CardDescription>Inspect indexed collections and review the documents available to local retrieval.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-5 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-3">
            {collectionsQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading collections…</p>
            ) : collectionsQuery.data?.collections.length ? (
              collectionsQuery.data.collections.map((collection) => (
                <button
                  key={collection.id}
                  type="button"
                  onClick={() => setSelectedCollectionId(collection.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    selectedCollectionId === collection.id ? "border-primary bg-primary/5" : "border-border bg-white/70 hover:bg-white"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold">{collection.name}</p>
                      <p className="text-sm text-muted-foreground">{collection.document_ids.length} documents</p>
                    </div>
                    <FolderOpen className="h-4 w-4 text-primary" />
                  </div>
                </button>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">No collections indexed yet.</p>
            )}
          </div>

          <div className="rounded-2xl border border-border bg-white/65 p-4">
            {detailsQuery.isLoading ? (
              <p className="text-sm text-muted-foreground">Select a collection to inspect its documents.</p>
            ) : detailsQuery.data ? (
              <div className="space-y-4">
                <div>
                  <p className="subtle-label">Selected collection</p>
                  <h3 className="text-xl">{detailsQuery.data.collection.name}</h3>
                  <p className="text-sm text-muted-foreground">
                    Created {formatDate(detailsQuery.data.collection.created_at)} • {detailsQuery.data.documents.length} indexed documents
                  </p>
                </div>
                <div className="space-y-3">
                  {detailsQuery.data.documents.map((document) => (
                    <div key={document.id} className="rounded-xl border border-border bg-white/80 p-4">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="font-semibold">{document.filename}</p>
                          <p className="text-sm text-muted-foreground">
                            {document.document_type.toUpperCase()} • {document.page_count ?? "n/a"} pages • uploaded {formatDate(document.upload_timestamp)}
                          </p>
                        </div>
                        <Files className="h-4 w-4 text-primary" />
                      </div>
                      <p className="mt-3 text-sm text-muted-foreground">{document.summary || "No summary available."}</p>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">Choose a collection to see its documents.</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
