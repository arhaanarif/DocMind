import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { FileText, Users, Calendar } from "lucide-react";

interface MetadataCardProps {
  metadata: {
    title?: string;
    authors?: string[];
    publicationDate?: string;
    pages?: number;
    journal?: string;
  };
}

const MetadataCard = ({ metadata }: MetadataCardProps) => {
  return (
    <Card className="shadow-card animate-fade-in">
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <FileText className="h-5 w-5 text-primary" />
          <span>Document Metadata</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {metadata.title && (
          <div>
            <h3 className="font-semibold text-foreground mb-1">Title</h3>
            <p className="text-muted-foreground">{metadata.title}</p>
          </div>
        )}
        
        {metadata.authors && metadata.authors.length > 0 && (
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <Users className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-foreground">Authors</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {metadata.authors.map((author, index) => (
                <Badge key={index} variant="secondary">
                  {author}
                </Badge>
              ))}
            </div>
          </div>
        )}
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {metadata.publicationDate && (
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <Calendar className="h-4 w-4 text-primary" />
                <h3 className="font-semibold text-foreground">Publication Date</h3>
              </div>
              <p className="text-muted-foreground">{metadata.publicationDate}</p>
            </div>
          )}
          
          {metadata.pages && (
            <div>
              <h3 className="font-semibold text-foreground mb-1">Pages</h3>
              <p className="text-muted-foreground">{metadata.pages}</p>
            </div>
          )}
        </div>
        
        {metadata.journal && (
          <div>
            <h3 className="font-semibold text-foreground mb-1">Journal</h3>
            <p className="text-muted-foreground">{metadata.journal}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default MetadataCard;