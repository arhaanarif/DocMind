import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, MessageCircle } from "lucide-react";

interface SummaryCardProps {
  summary: string[];
  suggestedQuestions: string[];
  onQuestionClick: (question: string) => void;
}

const SummaryCard = ({ summary, suggestedQuestions, onQuestionClick }: SummaryCardProps) => {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Summary Section */}
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <span>AI-Generated Summary</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {summary.map((point, index) => (
              <li key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-primary rounded-full mt-2 flex-shrink-0" />
                <p className="text-muted-foreground leading-relaxed">{point}</p>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Suggested Questions Section */}
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <MessageCircle className="h-5 w-5 text-primary" />
            <span>Suggested Questions</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3">
            {suggestedQuestions.map((question, index) => (
              <Badge
                key={index}
                variant="outline"
                className="p-3 cursor-pointer hover:bg-primary hover:text-primary-foreground transition-colors text-left justify-start h-auto"
                onClick={() => onQuestionClick(question)}
              >
                {question}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default SummaryCard;